from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from dairyos.finance.profitability.services.feed_opex_cost_service import FeedOpexCostService


def _finance_row(category: str, amount: float, timestamp: datetime, master_category: str = ""):
    return SimpleNamespace(
        transaction_type="EXPENSE",
        category=category,
        master_category=master_category,
        amount=amount,
        transaction_date=timestamp,
    )


def test_feed_opex_cost_service_excludes_expenses_before_requested_window():
    now = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
    milk = [SimpleNamespace(total_yield=1000.0, production_date=now)]
    finance = [
        _finance_row("FEED", 100.0, now),
        _finance_row("FEED", 900.0, now.replace(day=1)),
    ]

    result = FeedOpexCostService().evaluate(milk, finance, days=30, now=now)

    assert result["feed_cost"] == 100.0
    assert result["opex"] == 0.0
    assert result["total_operating_cost"] == 100.0
