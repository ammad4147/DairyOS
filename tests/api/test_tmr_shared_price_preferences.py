"""End-to-end coverage for the shared TMR ingredient price authority."""

from dairyos.api.tmr import SHARED_PRICE_PREFERENCE_GROUP
from dairyos.app import container


SILAGE = "Corn / Maize Silage"


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
