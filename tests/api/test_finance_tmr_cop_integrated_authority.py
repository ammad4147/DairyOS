"""Deep disposable-database proof for the Finance -> TMR -> COP authority chain."""

from datetime import date, datetime, time
from types import SimpleNamespace

from dairyos.api import farm_data_entry
from dairyos.api.tmr import lock_daily_tmr_cost_snapshot, tmr_feed_cost_for_period
from dairyos.app import container
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


SILAGE = "Corn / Maize Silage"
AUDIT_DATE = date(2040, 1, 15)


def test_period_feed_cost_uses_timestamped_feed_tab_logs_when_snapshot_is_missing(
    monkeypatch,
):
    """Known Feed-tab costs remain usable and gaps stay explicitly partial."""

    monkeypatch.setattr(
        OperationalDateAuthority,
        "current_date",
        lambda self: AUDIT_DATE,
    )
    factory = SimpleNamespace(
        feed=lambda: SimpleNamespace(
            get_all=lambda: [
                SimpleNamespace(
                    feeding_date=datetime(2040, 1, 14, 8, 0),
                    total_feed_cost=1200,
                ),
                SimpleNamespace(
                    feeding_date=datetime(2040, 1, 15, 8, 0),
                    total_feed_cost=800,
                ),
            ],
        ),
        feed_rations=lambda: SimpleNamespace(get_active_for_group=lambda group: []),
    )

    result = tmr_feed_cost_for_period(factory, date(2040, 1, 14), AUDIT_DATE)

    assert result["total_feed_cost"] == 2000
    assert result["complete"] is True
    assert [row["basis"] for row in result["daily"]] == [
        "FEED_TAB_DAILY_LOG",
        "FEED_TAB_DAILY_LOG",
    ]


def _feed_purchase(client, *, rate: float, reference: str):
    return client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "EXPENSE",
            "master_category": "FEED",
            "sub_category": SILAGE,
            "quantity": 1000,
            "unit": "kg",
            "unit_rate": rate,
            "transaction_date": AUDIT_DATE.isoformat(),
            "payment_method": "BANK",
            "counterparty": "Deep authority supplier",
            "reference": reference,
            "status": "PAID",
        },
    )


def test_finance_tmr_cop_chain_uses_active_purchase_snapshot_and_same_denominator(
    client,
    registered_animal,
    monkeypatch,
):
    """A real disposable chain reconciles purchase price, TMR snapshot and COP."""

    monkeypatch.setattr(
        OperationalDateAuthority,
        "current_date",
        lambda self: AUDIT_DATE,
    )
    monkeypatch.setattr(
        OperationalDateAuthority,
        "current_datetime",
        lambda self: datetime.combine(AUDIT_DATE, time(13, 0)),
    )
    monkeypatch.setattr(
        farm_data_entry,
        "_today_for_factory",
        lambda factory: AUDIT_DATE,
    )

    active_purchase = _feed_purchase(
        client,
        rate=20,
        reference="DEEP-FEED-20",
    )
    assert active_purchase.status_code == 200, active_purchase.text

    superseded_purchase = _feed_purchase(
        client,
        rate=4000,
        reference="DEEP-VOID-4000",
    )
    assert superseded_purchase.status_code == 200, superseded_purchase.text
    voided = client.post(
        f"/farm/finance-ledger/{superseded_purchase.json()['id']}/status",
        json={"status": "VOID", "reason": "Disposable audit supersession"},
    )
    assert voided.status_code == 200, voided.text

    latest_purchase = _feed_purchase(
        client,
        rate=25,
        reference="DEEP-FEED-25",
    )
    assert latest_purchase.status_code == 200, latest_purchase.text

    milk = client.post(
        "/farm/milk",
        json={
            "animal_id": registered_animal,
            "morning_yield": 100.0,
            "production_date": AUDIT_DATE.isoformat(),
            "operator": "Deep authority audit",
        },
    )
    assert milk.status_code == 200, milk.text

    opex = client.post(
        "/farm/finance-ledger",
        json={
            "transaction_type": "EXPENSE",
            "master_category": "OPEX",
            "sub_category": "Grid Electricity (WAPDA)",
            "quantity": 1,
            "unit": "service",
            "unit_rate": 500,
            "transaction_date": AUDIT_DATE.isoformat(),
            "payment_method": "CASH",
            "counterparty": "Deep authority utility",
            "reference": "DEEP-OPEX-500",
            "status": "PAID",
            "cop_classification": "OPEX",
            "cop_attribution_method": "DIRECT",
            "cop_service_date": AUDIT_DATE.isoformat(),
        },
    )
    assert opex.status_code == 200, opex.text

    live = client.get("/farm/tmr")
    assert live.status_code == 200, live.text
    live_summary = live.json()
    silage = next(
        ingredient
        for ingredient in live_summary["stages"]["early_milking"]["ingredients"]
        if ingredient["catalog_name"] == SILAGE
    )
    assert silage["price_per_kg"] == 25
    assert silage["price_source"] == "FINANCE"
    assert silage["finance_price_per_kg"] == 25
    assert silage["price_per_kg"] != 4000

    # TMR-01: catalog defaults are not costing authority. Explicit Manual rates
    # for remaining ingredients complete the ration so the Finance→snapshot→COP
    # chain can be certified without silent MANUAL_FALLBACK.
    early = live_summary["stages"]["early_milking"]
    stage_payload = {
        "stage": "early_milking",
        "operator": "Deep authority audit",
        "ingredients": [
            {
                "catalog_name": item["catalog_name"],
                "quantity": item["quantity"],
                "dose_unit": item["dose_unit"],
                "fallback_price_per_kg": float(
                    item.get("manual_price_per_kg")
                    or item.get("fallback_price_per_kg")
                    or 0
                ) or 1.0,
                "price_source": (
                    "FINANCE"
                    if item.get("finance_price_per_kg")
                    else "MANUAL"
                ),
            }
            for item in early["ingredients"]
        ],
        "shared_price_preferences": [
            {
                "catalog_name": item["catalog_name"],
                "fallback_price_per_kg": float(
                    item.get("manual_price_per_kg")
                    or item.get("fallback_price_per_kg")
                    or 0
                ) or 1.0,
                "price_source": (
                    "FINANCE"
                    if item.get("finance_price_per_kg")
                    else "MANUAL"
                ),
            }
            for item in early["ingredients"]
        ],
    }
    saved = client.post("/farm/tmr/stages", json=stage_payload)
    assert saved.status_code == 200, saved.text
    live = client.get("/farm/tmr")
    assert live.status_code == 200, live.text
    live_summary = live.json()
    assert live_summary.get("costing_complete") is True

    storage = client.get("/farm/feed-inventory/dashboard")
    assert storage.status_code == 200, storage.text
    silage_stock = next(
        item for item in storage.json()["items"] if item["item"] == SILAGE
    )
    assert silage_stock["purchased_from_finance"] == 2000
    assert silage_stock["balance"] == 2000
    assert silage_stock["latest_finance_unit_rate"] == 25

    milking_category = next(
        category
        for category in live_summary["categories"]
        if category["category"] == "Milking"
    )
    expected_head_cost = round(
        sum(
            live_summary["stages"][stage]["cost_per_head_day"]
            for stage in milking_category["stage_keys"]
        )
        / len(milking_category["stage_keys"]),
        4,
    )
    assert milking_category["animal_count"] == 1
    assert milking_category["cost_per_head_day"] == expected_head_cost
    assert milking_category["category_cost_per_day"] == expected_head_cost
    assert live_summary["total_herd_feed_cost_per_day"] == round(
        sum(category["category_cost_per_day"] for category in live_summary["categories"]),
        4,
    )

    factory = container.repository_factory
    snapshot = lock_daily_tmr_cost_snapshot(
        factory,
        operational_date=AUDIT_DATE,
    )
    assert snapshot["locked"] is True
    assert snapshot["basis"] == "GOVERNED_TMR_X_ACTIVE_HERD_AT_12_00"
    assert snapshot["total_herd_feed_cost_per_day"] == live_summary[
        "total_herd_feed_cost_per_day"
    ]

    feed_basis = tmr_feed_cost_for_period(
        factory,
        AUDIT_DATE,
        AUDIT_DATE,
    )
    assert feed_basis["complete"] is True
    assert feed_basis["locked_days"] == 1
    assert feed_basis["daily"][0]["basis"] == "LOCKED_DAILY_TMR"
    assert feed_basis["total_feed_cost"] == snapshot[
        "total_herd_feed_cost_per_day"
    ]

    cop = client.get(
        "/farm/coml/integrated",
        params={
            "period_start": AUDIT_DATE.isoformat(),
            "period_end": AUDIT_DATE.isoformat(),
            "allow_current_period": "true",
        },
    )
    assert cop.status_code == 200, cop.text
    cop_body = cop.json()
    assert cop_body["production"]["totalLiters"] == 100
    assert cop_body["costs"]["feed_total"] == round(
        snapshot["total_herd_feed_cost_per_day"],
        2,
    )
    assert cop_body["costs"]["opex_total"] == 500
    assert cop_body["costs"]["feed_source"]["daily"][0]["basis"] == "LOCKED_DAILY_TMR"
    assert cop_body["costs"]["feed_cost_per_liter"] == round(
        snapshot["total_herd_feed_cost_per_day"] / 100,
        4,
    )
    assert cop_body["costs"]["opex_cost_per_liter"] == 5
    assert cop_body["costs"]["total_coml_per_liter"] == round(
        (snapshot["total_herd_feed_cost_per_day"] + 500) / 100,
        4,
    )
    assert cop_body["costs"]["source"] == "TMR_HERD_COST+FINANCE_OPEX"

def test_persisted_historical_non_opex_is_excluded_without_reclassification(
    client,
    monkeypatch,
):
    from decimal import Decimal

    from dairyos.api import coml as coml_api
    from dairyos.data.models.financial_transaction import FinancialTransaction

    # AUDIT_DATE is intentionally future-dated relative to the real clock.
    # Establish it as the governed farm operational date, matching the
    # authority setup used by the deep integration test above.
    monkeypatch.setattr(
        OperationalDateAuthority,
        "current_date",
        lambda self: AUDIT_DATE,
    )
    monkeypatch.setattr(
        OperationalDateAuthority,
        "current_datetime",
        lambda self: datetime.combine(AUDIT_DATE, time(13, 0)),
    )

    historical = FinancialTransaction(
        transaction_type="EXPENSE",
        category="EQUIPMENT",
        amount=Decimal("750000.00"),
        transaction_date=datetime.combine(
            AUDIT_DATE,
            time.min,
        ),
        status="RECORDED",
        master_category="OPEX",
        sub_category="Equipment Purchase",
        cop_classification="NON_OPEX",
    )

    session = container.repository_factory.session
    session.add(historical)
    session.commit()
    session.refresh(historical)

    historical_id = historical.id

    # Keep this contract focused on persisted Finance compatibility.
    # The existing test above independently proves the real Milk/TMR/
    # Finance -> integrated COML chain.
    monkeypatch.setattr(
        coml_api,
        "tmr_feed_cost_for_period",
        lambda factory, start, end: {
            "total_feed_cost": 0.0,
            "complete": True,
            "locked_days": 1,
            "missing_days": [],
            "daily": [],
        },
    )
    monkeypatch.setattr(
        coml_api,
        "milk_litres_for_period",
        lambda factory, start, end: 100.0,
    )

    response = client.get(
        "/farm/coml/integrated",
        params={
            "period_start": AUDIT_DATE.isoformat(),
            "period_end": AUDIT_DATE.isoformat(),
            "allow_current_period": "true",
        },
    )

    assert response.status_code == 200, response.text

    costs = response.json()["costs"]

    assert costs["opex_total"] == 0.0
    assert costs["non_opex_excluded_total"] == 750000.0
    assert costs["unattributed_opex_total"] == 0.0
    assert costs["unattributed_opex_count"] == 0

    # Integrated COML must interpret the historical row, not rewrite it.
    session.expire_all()

    persisted = session.get(
        FinancialTransaction,
        historical_id,
    )

    assert persisted is not None
    assert persisted.master_category == "OPEX"
    assert persisted.sub_category == "Equipment Purchase"
    assert persisted.cop_classification == "NON_OPEX"
    assert persisted.status == "RECORDED"
    assert Decimal(str(persisted.amount)) == Decimal("750000.00")
