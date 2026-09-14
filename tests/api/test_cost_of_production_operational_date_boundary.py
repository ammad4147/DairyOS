"""COP period boundaries follow the farm operational date, not UTC wall date."""

from datetime import UTC, datetime

from dairyos.finance.profitability.services.feed_opex_cost_service import (
    FeedOpexCostService,
)


class _Milk:
    production_date = datetime(2026, 9, 10, 0, 0)
    total_yield = 100.0
    status = "RECORDED"


class _Expense:
    transaction_date = datetime(2026, 9, 10, 0, 0)
    transaction_type = "EXPENSE"
    amount = 1000.0
    category = "FEED"
    master_category = "FEED"
    cop_classification = None
    cop_attribution_method = None
    cop_service_date = None
    cop_coverage_start = None
    cop_coverage_end = None


def test_farm_operational_day_end_includes_same_day_records_after_utc_rollover():
    # At 19:10 UTC on Sep 9 it is already Sep 10 in Pakistan. Endpoints must
    # pass Sep 10 farm-day end into the COP service rather than raw UTC "now".
    farm_day_end = datetime(2026, 9, 10, 23, 59, 59, 999999, tzinfo=UTC)

    result = FeedOpexCostService().evaluate(
        [_Milk()],
        [_Expense()],
        days=30,
        now=farm_day_end,
        governed_feed_cost=1000.0,
        feed_authority_complete=True,
        period_start=datetime(2026, 8, 12).date(),
        period_end=datetime(2026, 9, 10).date(),
    )

    assert result["milk_litres"] == 100.0
    assert result["feed_cost"] == 1000.0
    assert result["feed_cost_per_litre"] == 10.0
    assert result["feed_cost_authority"] == "GOVERNED_TMR_CONSUMPTION"

def test_cop_milk_denominator_excludes_day_before_operational_period():
    class BeforePeriodMilk:
        production_date = datetime(2026, 8, 11, 23, 59, 59)
        total_yield = 900.0
        status = "RECORDED"

    class FirstDayMilk:
        production_date = datetime(2026, 8, 12, 0, 0)
        total_yield = 100.0
        status = "RECORDED"

    period_start = datetime(2026, 8, 12).date()
    period_end = datetime(2026, 9, 10).date()
    period_day_end = datetime(
        2026,
        9,
        10,
        23,
        59,
        59,
        999999,
        tzinfo=UTC,
    )

    result = FeedOpexCostService().evaluate(
        [BeforePeriodMilk(), FirstDayMilk()],
        [],
        days=30,
        now=period_day_end,
        governed_feed_cost=1000.0,
        feed_authority_complete=True,
        period_start=period_start,
        period_end=period_end,
    )

    assert result["milk_litres"] == 100.0
    assert result["period_days"] == 30
    assert result["from"] == "2026-08-12"
    assert result["to"] == "2026-09-10"
    assert result["feed_cost_per_litre"] == 10.0


def test_cop_missing_tmr_authority_fails_closed():
    result = FeedOpexCostService().evaluate(
        [_Milk()],
        [_Expense()],
        days=30,
        now=datetime(
            2026,
            9,
            10,
            23,
            59,
            59,
            999999,
            tzinfo=UTC,
        ),
        governed_feed_cost=None,
        feed_authority_complete=False,
        period_start=datetime(2026, 8, 12).date(),
        period_end=datetime(2026, 9, 10).date(),
    )

    assert result["milk_litres"] == 100.0
    assert result["feed_cost"] is None
    assert result["feed_cost_per_litre"] is None
    assert result["total_operating_cost"] is None
    assert result["cost_per_litre"] is None
    assert result["cmpl"] is None
    assert result["feed_authority_complete"] is False
    assert result["feed_cost_authority"] == "MISSING_TMR_AUTHORITY"


def test_governed_cop_uses_one_period_authority_for_legacy_reporting_fields():
    """
    COP-SEM-01 regression.

    Every field returned by FeedOpexCostService must describe the same
    inclusive operational-date period. Out-of-period Milk and Finance rows
    must not leak through the inherited legacy reporting payload.
    """
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from dairyos.finance.profitability.services.feed_opex_cost_service import (
        FeedOpexCostService,
    )

    period_start = datetime(2026, 9, 10).date()
    period_end = datetime(2026, 9, 10).date()

    in_period_milk = SimpleNamespace(
        production_date=datetime(
            2026, 9, 10, 8, 0, tzinfo=UTC
        ),
        total_yield=100.0,
        status="RECORDED",
    )

    outside_milk = SimpleNamespace(
        production_date=datetime(
            2026, 9, 9, 8, 0, tzinfo=UTC
        ),
        total_yield=900.0,
        status="RECORDED",
    )

    in_period_withdrawal = SimpleNamespace(
        transaction_date=datetime(
            2026, 9, 10, 12, 0, tzinfo=UTC
        ),
        transaction_type="OWNER_WITHDRAWAL",
        type="OWNER_WITHDRAWAL",
        amount=9000.0,
        category="OTHER_OPERATING",
        master_category="",
        status="POSTED",
    )

    outside_withdrawal = SimpleNamespace(
        transaction_date=datetime(
            2026, 9, 9, 12, 0, tzinfo=UTC
        ),
        transaction_type="OWNER_WITHDRAWAL",
        type="OWNER_WITHDRAWAL",
        amount=8000.0,
        category="OTHER_OPERATING",
        master_category="",
        status="POSTED",
    )

    result = FeedOpexCostService().evaluate(
        [
            outside_milk,
            in_period_milk,
        ],
        [
            outside_withdrawal,
            in_period_withdrawal,
        ],
        days=1,
        now=datetime(
            2026,
            9,
            10,
            23,
            59,
            59,
            999999,
            tzinfo=UTC,
        ),
        governed_feed_cost=1000.0,
        feed_authority_complete=True,
        period_start=period_start,
        period_end=period_end,
    )

    # Authoritative milk/COP period.
    assert result["milk_litres"] == 100.0
    assert result["period_days"] == 1
    assert result["from"] == "2026-09-10"
    assert result["to"] == "2026-09-10"
    assert result["feed_cost"] == 1000.0
    assert result["feed_cost_per_litre"] == 10.0
    assert result["cost_per_litre"] == 10.0

    # Inherited Finance reporting must use exactly the same period.
    assert result["non_operating_outflow_count"] == 1
    assert result["non_operating_outflow_total"] == 9000.0
