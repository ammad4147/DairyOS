"""Feed/OPEX profitability metrics using governed TMR and Finance OPEX."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.finance.opex_attribution import attributed_amount
from dairyos.finance.profitability.services.cost_of_production_service import (
    CostOfProductionService,
)


class FeedOpexCostService:
    """
    Calculate authoritative farm COP from explicit domain authorities.

    Feed:
        governed TMR consumption cost supplied by the caller.

    OPEX:
        attributable Finance OPEX for the requested period.

    Finance FEED purchases remain accounting/inventory evidence and are never
    treated as feed-consumption cost by this service.
    """

    def __init__(self) -> None:
        self.base = CostOfProductionService()

    def evaluate(
        self,
        milk_records,
        financial_records,
        days: int = 30,
        now: datetime | None = None,
        *,
        governed_feed_cost: float | Decimal | None,
        feed_authority_complete: bool,
        period_start: date | None = None,
        period_end: date | None = None,
    ):
        if days < 1:
            raise ValueError("days must be positive")

        now_dt = CostOfProductionService._as_utc(
            now or datetime.now(UTC)
        )

        if period_end is None:
            period_end = now_dt.date()

        if period_start is None:
            period_start = period_end - timedelta(
                days=days - 1
            )

        if period_end < period_start:
            raise ValueError(
                "period_end cannot be earlier than period_start"
            )

        # The governed service uses an inclusive operational-date period.
        # Every field exposed in this response must describe that same period,
        # including informational fields inherited from the legacy service.
        #
        # Pre-filter Finance rows to the governed date interval before invoking
        # the legacy reporting helper.  Its rolling timestamp window is widened
        # deliberately so it cannot discard a row that has already passed the
        # authoritative operational-date filter.
        governed_financial_records = [
            row
            for row in financial_records
            if (
                transaction_date := getattr(
                    row,
                    "transaction_date",
                    None,
                )
            )
            is not None
            and period_start
            <= (
                transaction_date.date()
                if isinstance(transaction_date, datetime)
                else transaction_date
            )
            <= period_end
        ]

        # Authoritative COP periods are operational-date periods.  TMR feed,
        # Finance reporting, Finance OPEX and the milk denominator must all use
        # this same inclusive period_start..period_end authority.
        governed_milk = [
            row
            for row in milk_records
            if (
                production_date := getattr(
                    row,
                    "production_date",
                    None,
                )
            )
            is not None
            and period_start
            <= (
                production_date.date()
                if isinstance(production_date, datetime)
                else production_date
            )
            <= period_end
            and str(
                getattr(
                    row,
                    "status",
                    "RECORDED",
                )
                or "RECORDED"
            ).upper()
            in {
                "RECORDED",
                "SOLD",
                "DISPOSED",
                "WASTAGE",
                "WITHDRAWAL",
            }
        ]

        # Feed the legacy reporting helper only records already admitted by
        # the governed operational-date boundary.  The deliberately widened
        # timestamp window below is therefore only a compatibility mechanism;
        # it cannot admit an out-of-period Milk or Finance row.
        result = self.base.evaluate(
            governed_milk,
            governed_financial_records,
            days=max(
                days,
                (period_end - period_start).days + 2,
            ),
            now=datetime.combine(
                period_end,
                datetime.max.time(),
                tzinfo=UTC,
            ),
        )

        volume = sum(
            max(
                0.0,
                float(
                    getattr(
                        row,
                        "total_yield",
                        0.0,
                    )
                    or 0.0
                ),
            )
            for row in governed_milk
        )

        # Keep the inherited informational payload internally coherent with
        # the authoritative denominator used by Feed Cost/L, OPEX/L and COP/L.
        result["milk_litres"] = round(
            volume,
            3,
        )
        result["period_days"] = (
            period_end - period_start
        ).days + 1
        result["from"] = period_start.isoformat()
        result["to"] = period_end.isoformat()

        feed_cost = (
            Decimal(str(governed_feed_cost)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            if (
                feed_authority_complete
                and governed_feed_cost is not None
            )
            else None
        )

        opex_cost = Decimal("0.00")
        unattributed_opex = Decimal("0.00")
        non_opex_excluded = Decimal("0.00")

        for row in governed_financial_records:
            if not classifier.is_expense(row):
                continue

            master = str(
                getattr(row, "master_category", "")
                or ""
            ).strip().upper()

            # Finance FEED transactions are purchase/inventory evidence.
            # Governed TMR consumption supplied above is the sole Feed COP
            # authority.
            if master == "FEED":
                continue

            if master not in {"OPEX", "NON_OPEX"}:
                continue

            amount = Decimal(
                str(getattr(row, "amount", 0) or 0)
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            attributed, status = attributed_amount(
                row,
                period_start,
                period_end,
            )

            if status == "ATTRIBUTED":
                opex_cost += attributed
            elif status == "UNATTRIBUTED":
                unattributed_opex += amount
            elif status == "NON_OPEX":
                non_opex_excluded += amount

        total = (
            feed_cost + opex_cost
            if feed_cost is not None
            else None
        )

        volume_decimal = Decimal(str(volume))

        feed_per_litre = (
            (feed_cost / volume_decimal).quantize(
                Decimal("0.000001"),
                rounding=ROUND_HALF_UP,
            )
            if (
                feed_cost is not None
                and volume_decimal > 0
            )
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
            if (
                total is not None
                and volume_decimal > 0
            )
            else None
        )

        authoritative_cop = (
            float(total_per_litre)
            if total_per_litre is not None
            else None
        )

        return {
            **result,
            # Override the legacy generic Finance-expense COP result.
            "cost_per_litre": authoritative_cop,
            "feed_cost": (
                float(feed_cost)
                if feed_cost is not None
                else None
            ),
            "opex": float(opex_cost),
            "unattributed_opex": float(
                unattributed_opex
            ),
            "non_opex_excluded": float(
                non_opex_excluded
            ),
            "total_operating_cost": (
                float(total)
                if total is not None
                else None
            ),
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
            "cmpl": authoritative_cop,
            "feed_authority_complete": bool(
                feed_authority_complete
            ),
            "feed_cost_authority": (
                "GOVERNED_TMR_CONSUMPTION"
                if feed_authority_complete
                else "MISSING_TMR_AUTHORITY"
            ),
        }
