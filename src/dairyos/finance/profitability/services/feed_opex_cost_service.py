"""Feed/OPEX-aware profitability metrics layered on the existing cost engine."""
# AUDIT-FIX [LOGIC-FIN-01]: Ensure financial_records are filtered by the requested
# 'days' time window using normalized UTC timestamps, matching CostOfProductionService.
# Prevents historical all-time expenses from inflating period-bounded cost-per-litre.
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

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

        feed_cost = Decimal("0.00")
        opex_cost = Decimal("0.00")

        # AUDIT-FIX [LOGIC-FIN-01]: Filter financial transactions to the specified period cutoff
        for row in financial_records:
            if not classifier.is_expense(row):
                continue

            timestamp = CostOfProductionService._as_utc(getattr(row, "transaction_date", None))
            if timestamp is None or timestamp < cutoff:
                continue

            master = str(getattr(row, "master_category", "") or "").strip().upper()
            category = str(getattr(row, "category", "") or "").strip().upper()
            amount = Decimal(
                getattr(row, "amount", 0) or 0
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            if master == "FEED" or (not master and category == "FEED"):
                feed_cost += amount
            elif master == "OPEX" or (not master and category in {
                "HEALTH", "BREEDING", "LABOUR", "UTILITIES", "EQUIPMENT", "OTHER_OPERATING"
            }):
                opex_cost += amount

        total = feed_cost + opex_cost
        volume_decimal = Decimal(str(volume))

        feed_per_litre = (
            (feed_cost / volume_decimal).quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP,
            )
            if volume_decimal > 0
            else None
        )
        opex_per_litre = (
            (opex_cost / volume_decimal).quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP,
            )
            if volume_decimal > 0
            else None
        )
        total_per_litre = (
            (total / volume_decimal).quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP,
            )
            if volume_decimal > 0
            else None
        )

        return {
            **result,
            "feed_cost": float(feed_cost),
            "opex": float(opex_cost),
            "total_operating_cost": float(total),
            "feed_cost_per_litre": (
                float(feed_per_litre)
                if feed_per_litre is not None
                else None
            ),
            "opex_cost_per_litre": (
                float(opex_per_litre)
                if opex_per_litre is not None
                else None
            ),
            "cmpl": (
                float(total_per_litre)
                if total_per_litre is not None
                else None
            ),
        }
