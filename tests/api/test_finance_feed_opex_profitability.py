from datetime import UTC, date, datetime
from types import SimpleNamespace

from dairyos.api.finance_ledger import feed_opex_profitability


class _Repository:
    def __init__(self, rows):
        self.rows = rows

    def get_all(self):
        return self.rows


class _Factory:
    def __init__(self, milk_rows, finance_rows):
        self._milk = _Repository(milk_rows)
        self._finance = _Repository(finance_rows)

    def milk(self):
        return self._milk

    def finance(self):
        return self._finance


class _Container:
    def __init__(self, factory):
        self.repository_factory = factory


def test_feed_opex_profitability_uses_persisted_records_for_requested_period():
    factory = _Factory(
        [
            SimpleNamespace(
                production_date=datetime(2026, 9, 1, tzinfo=UTC),
                total_yield=100.0,
                status="RECORDED",
            )
        ],
        [
            SimpleNamespace(
                transaction_date=datetime(2026, 9, 1, tzinfo=UTC),
                transaction_type="EXPENSE",
                master_category="FEED",
                category="FEED",
                amount=2500.0,
                status="PAID",
            )
        ],
    )

    result = feed_opex_profitability(
        date(2026, 9, 1),
        date(2026, 9, 1),
        container=_Container(factory),
    )

    assert result["feed_cost"] == 2500.0
    assert result["feed_cost_per_litre"] == 25.0
