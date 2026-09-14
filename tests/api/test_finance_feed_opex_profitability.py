from datetime import UTC, date, datetime
from types import SimpleNamespace

import dairyos.api.finance_ledger as finance_ledger_api
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


def test_feed_opex_profitability_uses_governed_tmr_for_requested_period(
    monkeypatch,
):
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

    captured = {}

    def governed_tmr(factory_arg, start, end):
        captured["factory"] = factory_arg
        captured["start"] = start
        captured["end"] = end
        return {
            "total_feed_cost": 1200.0,
            "complete": True,
            "missing_authority_days": [],
            "source": "TEST_GOVERNED_TMR",
        }

    monkeypatch.setattr(
        finance_ledger_api,
        "tmr_feed_cost_for_period",
        governed_tmr,
    )

    result = feed_opex_profitability(
        date(2026, 9, 1),
        date(2026, 9, 1),
        container=_Container(factory),
    )

    assert captured["factory"] is factory
    assert captured["start"] == date(2026, 9, 1)
    assert captured["end"] == date(2026, 9, 1)

    assert result["milk_litres"] == 100
    assert result["feed_cost"] == 1200
    assert result["feed_cost_per_litre"] == 12
    assert result["opex"] == 0
    assert result["total_operating_cost"] == 1200
    assert result["cost_per_litre"] == 12
    assert result["cmpl"] == 12
    assert result["feed_authority_complete"] is True
    assert result["feed_cost_authority"] == "GOVERNED_TMR_CONSUMPTION"
