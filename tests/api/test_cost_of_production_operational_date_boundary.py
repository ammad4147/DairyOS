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
    )

    assert result["milk_litres"] == 100.0
    assert result["cost_per_litre"] == 10.0
    assert result["feed_cost_per_litre"] == 10.0
