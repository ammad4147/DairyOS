"""End-to-end coverage for the shared TMR ingredient price authority."""

from dairyos.api.tmr import SHARED_PRICE_PREFERENCE_GROUP
from dairyos.app import container


SILAGE = "Corn / Maize Silage"
VANDA = "Commercial Compound Vanda / Cattle Feed"


def _stage_payload(summary, *, source: str, manual_rate: float):
    stage = summary["stages"]["early_milking"]
    ingredients = [
        {
            "catalog_name": row["catalog_name"],
            "quantity": row["quantity"],
            "dose_unit": row["dose_unit"],
            "fallback_price_per_kg": (
                manual_rate
                if row["catalog_name"] == SILAGE
                else row.get("manual_price_per_kg", row["fallback_price_per_kg"])
            ),
            "price_source": (
                source if row["catalog_name"] == SILAGE else row["selected_price_source"]
            ),
        }
        for row in stage["ingredients"]
    ]
    return {
        "stage": "early_milking",
        "operator": "TMR shared-price regression",
        "ingredients": ingredients,
        "shared_price_preferences": [
            {
                "catalog_name": SILAGE,
                "fallback_price_per_kg": manual_rate,
                "price_source": source,
            }
        ],
    }


def _ingredient(summary, stage: str, name: str = SILAGE):
    return next(
        row
        for row in summary["stages"][stage]["ingredients"]
        if row["catalog_name"] == name
    )


def test_price_source_change_is_shared_and_survives_reload(client):
    finance_purchase = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "EXPENSE",
            "master_category": "FEED",
            "sub_category": SILAGE,
            "quantity": 1000,
            "unit": "kg",
            "unit_rate": 20,
            "transaction_date": "2026-09-15",
            "payment_method": "BANK",
            "counterparty": "Shared-price regression supplier",
            "reference": "TMR-SHARED-001",
        },
    )
    assert finance_purchase.status_code == 200, finance_purchase.text

    initial = client.get("/farm/tmr")
    assert initial.status_code == 200, initial.text
    initial_summary = initial.json()
    assert _ingredient(initial_summary, "early_milking")["price_per_kg"] == 20

    manual_save = client.post(
        "/farm/tmr/stages",
        json=_stage_payload(initial_summary, source="MANUAL", manual_rate=35),
    )
    assert manual_save.status_code == 200, manual_save.text
    assert manual_save.json()["shared_price_preference_record_id"]

    manual_summary = client.get("/farm/tmr").json()
    assert manual_summary["shared_price_preferences"][SILAGE] == {
        "selected_price_source": "MANUAL",
        "manual_price_per_kg": 35,
    }
    for stage in manual_summary["stages"]:
        row = _ingredient(manual_summary, stage)
        assert row["selected_price_source"] == "MANUAL"
        assert row["price_source"] == "MANUAL"
        assert row["price_per_kg"] == 35

    shared_records = [
        row
        for row in container.repository_factory.feed_rations().get_all()
        if row.animal_group == SHARED_PRICE_PREFERENCE_GROUP
    ]
    assert shared_records
    visible_rations = client.get("/farm/feed/rations")
    assert visible_rations.status_code == 200, visible_rations.text
    assert all(
        row["animal_group"] != SHARED_PRICE_PREFERENCE_GROUP
        for row in visible_rations.json()
    )

    finance_save = client.post(
        "/farm/tmr/stages",
        json=_stage_payload(manual_summary, source="FINANCE", manual_rate=35),
    )
    assert finance_save.status_code == 200, finance_save.text

    finance_summary = client.get("/farm/tmr").json()
    for stage in finance_summary["stages"]:
        row = _ingredient(finance_summary, stage)
        assert row["selected_price_source"] == "FINANCE"
        assert row["price_source"] == "FINANCE"
        assert row["price_per_kg"] == 20


def test_new_finance_purchase_promotes_only_that_ingredient_and_survives_reload(
    client,
):
    silage_purchase = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "EXPENSE",
            "master_category": "FEED",
            "sub_category": SILAGE,
            "quantity": 1000,
            "unit": "kg",
            "unit_rate": 20,
            "transaction_date": "2026-09-15",
            "payment_method": "BANK",
            "counterparty": "Finance preference supplier",
            "reference": "TMR-AUTO-FINANCE-20",
        },
    )
    assert silage_purchase.status_code == 200, silage_purchase.text

    vanda_purchase = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "EXPENSE",
            "master_category": "FEED",
            "sub_category": VANDA,
            "quantity": 1000,
            "unit": "kg",
            "unit_rate": 100,
            "transaction_date": "2026-09-15",
            "payment_method": "BANK",
            "counterparty": "Finance preference supplier",
            "reference": "TMR-AUTO-FINANCE-VANDA",
        },
    )
    assert vanda_purchase.status_code == 200, vanda_purchase.text

    initial = client.get("/farm/tmr")
    assert initial.status_code == 200, initial.text
    manual_payload = _stage_payload(initial.json(), source="MANUAL", manual_rate=35)
    for row in manual_payload["ingredients"]:
        if row["catalog_name"] == VANDA:
            row["fallback_price_per_kg"] = 150
            row["price_source"] = "MANUAL"
    manual_payload["shared_price_preferences"].append(
        {
            "catalog_name": VANDA,
            "fallback_price_per_kg": 150,
            "price_source": "MANUAL",
        }
    )
    manual_save = client.post("/farm/tmr/stages", json=manual_payload)
    assert manual_save.status_code == 200, manual_save.text

    manual_summary = client.get("/farm/tmr").json()
    for stage in manual_summary["stages"]:
        assert _ingredient(manual_summary, stage, SILAGE)["price_source"] == "MANUAL"
        assert _ingredient(manual_summary, stage, VANDA)["price_source"] == "MANUAL"

    new_silage_purchase = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "EXPENSE",
            "master_category": "FEED",
            "sub_category": SILAGE,
            "quantity": 500,
            "unit": "kg",
            "unit_rate": 25,
            "transaction_date": "2026-09-15",
            "payment_method": "BANK",
            "counterparty": "Finance preference supplier",
            "reference": "TMR-AUTO-FINANCE-25",
        },
    )
    assert new_silage_purchase.status_code == 200, new_silage_purchase.text

    promoted = client.get("/farm/tmr")
    assert promoted.status_code == 200, promoted.text
    promoted_summary = promoted.json()
    assert promoted_summary["shared_price_preferences"][SILAGE] == {
        "selected_price_source": "FINANCE",
        "manual_price_per_kg": 35,
    }
    assert promoted_summary["shared_price_preferences"][VANDA] == {
        "selected_price_source": "MANUAL",
        "manual_price_per_kg": 150,
    }
    for stage in promoted_summary["stages"]:
        silage = _ingredient(promoted_summary, stage, SILAGE)
        vanda = _ingredient(promoted_summary, stage, VANDA)
        assert silage["selected_price_source"] == "FINANCE"
        assert silage["price_source"] == "FINANCE"
        assert silage["price_per_kg"] == 25
        assert vanda["selected_price_source"] == "MANUAL"
        assert vanda["price_source"] == "MANUAL"
        assert vanda["price_per_kg"] == 150
