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
        _finance_row("FEED", 900.0, datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)),
        _finance_row("HEALTH", 50.0, now, master_category="OPEX"),
        _finance_row("HEALTH", 900.0, datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc), master_category="OPEX"),
    ]

    result = FeedOpexCostService().evaluate(milk, finance, days=30, now=now)

    assert result["feed_cost"] == 100.0
    assert result["opex"] == 50.0
    assert result["total_operating_cost"] == 150.0
    assert result["cmpl"] == 0.15
