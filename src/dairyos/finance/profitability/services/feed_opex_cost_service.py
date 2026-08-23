"""Feed/OPEX-aware profitability metrics layered on the existing cost engine."""
# AUDIT-FIX [LOGIC-FIN-01]: Ensure financial_records are filtered by the requested
# 'days' time window using normalized UTC timestamps, matching CostOfProductionService.
# Prevents historical all-time expenses from inflating period-bounded cost-per-litre.
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.finance.profitability.services.cost_of_production_service import CostOfProductionService


class FeedOpexCostService:
    """Preserve the existing cost-of-production engine and add Feed/OPEX splits."""

    def __init__(self) -> None:
        self.base = CostOfProductionService()

    def evaluate(self, milk_records, financial_records, days: int = 30, now: datetime | None = None):
        if days < 1:
            raise ValueError("days must be positive")

        now_dt = CostOfProductionService._as_utc(now or datetime.now(timezone.utc))
        cutoff = now_dt - timedelta(days=days)

        result = self.base.evaluate(milk_records, financial_records, days=days, now=now_dt)
        volume = float(result.get("milk_litres") or 0.0)

        feed_cost = 0.0
        opex_cost = 0.0

        # AUDIT-FIX [LOGIC-FIN-01]: Filter financial transactions to the specified period cutoff
        for row in financial_records:
            if not classifier.is_expense(row):
                continue

            timestamp = CostOfProductionService._as_utc(getattr(row, "transaction_date", None))
            if timestamp is None or timestamp < cutoff:
                continue

            master = str(getattr(row, "master_category", "") or "").strip().upper()
            category = str(getattr(row, "category", "") or "").strip().upper()
            amount = float(getattr(row, "amount", 0.0) or 0.0)
            if master == "FEED" or (not master and category == "FEED"):
                feed_cost += amount
            elif master == "OPEX" or (not master and category in {
                "HEALTH", "BREEDING", "LABOUR", "UTILITIES", "EQUIPMENT", "OTHER_OPERATING"
            }):
                opex_cost += amount

        total = feed_cost + opex_cost
        return {
            **result,
            "feed_cost": round(feed_cost, 2),
            "opex": round(opex_cost, 2),
            "total_operating_cost": round(total, 2),
            "feed_cost_per_litre": round(feed_cost / volume, 4) if volume > 0 else None,
            "opex_cost_per_litre": round(opex_cost / volume, 4) if volume > 0 else None,
            "cmpl": round(total / volume, 4) if volume > 0 else None,
        }
