"""Feed/OPEX-aware profitability metrics layered on the existing cost engine."""
from __future__ import annotations

from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.finance.profitability.services.cost_of_production_service import CostOfProductionService


class FeedOpexCostService:
    """Preserve the existing cost-of-production engine and add Feed/OPEX splits."""

    def __init__(self) -> None:
        self.base = CostOfProductionService()

    def evaluate(self, milk_records, financial_records, days: int = 30):
        result = self.base.evaluate(milk_records, financial_records, days=days)
        volume = float(result.get("milk_litres") or 0.0)

        feed_cost = 0.0
        opex_cost = 0.0
        for row in financial_records:
            if not classifier.is_expense(row):
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
