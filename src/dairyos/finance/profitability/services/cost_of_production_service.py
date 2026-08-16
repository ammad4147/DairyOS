from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from dairyos.finance.classification import transaction_classifier as classifier


class CostOfProductionService:
    """Derive cost-of-production metrics only from persisted farm records.

    Milk production is counted from persisted milk records that contain actual
    production. Veterinary non-milking directives remove animals from the
    governed production population upstream; they do not create a special milk
    status here.
    """

    MILK_REVENUE_CATEGORIES = {
        "MILK",
        "MILK SALE",
        "MILK SALES",
        "MILK_SALES",
        "DAIRY SALES",
    }

    COST_DOMAIN_CATEGORIES = {
        "FEED": {"FEED", "FEEDING"},
        "LABOUR": {
            "LABOUR",
            "LABOR",
            "WORKFORCE",
            "WAGES",
            "SALARY",
            "SALARIES",
        },
        "HEALTH": {
            "VETERINARY",
            "VET",
            "HEALTH",
            "MEDICINE",
            "TREATMENT",
        },
        "BREEDING": {
            "BREEDING",
            "REPRODUCTION",
            "SEMEN",
        },
        "UTILITIES": {
            "UTILITIES",
            "ELECTRICITY",
            "WATER",
            "FUEL",
        },
        "EQUIPMENT": {
            "EQUIPMENT",
            "REPAIRS",
            "MAINTENANCE",
            "MACHINERY",
        },
        "OTHER_OPERATING": {
            "OTHER",
            "GENERAL",
            "OPERATING",
            "OTHER OPERATING",
            "OTHER_OPERATING",
        },
    }

    @staticmethod
    def _as_utc(
        value: datetime | None,
    ) -> datetime | None:
        """Normalize persisted naive/aware timestamps to UTC."""
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    def evaluate(
        self,
        milk_records,
        financial_records,
        days: int = 30,
        now: datetime | None = None,
    ):
        if days < 1:
            raise ValueError("days must be positive")

        now = self._as_utc(
            now or datetime.now(timezone.utc)
        )

        cutoff = now - timedelta(days=days)

        milk = [
            row
            for row in milk_records
            if (
                timestamp := self._as_utc(
                    getattr(
                        row,
                        "production_date",
                        None,
                    )
                )
            ) is not None
            and timestamp >= cutoff
        ]

        finance = [
            row
            for row in financial_records
            if (
                timestamp := self._as_utc(
                    getattr(
                        row,
                        "transaction_date",
                        None,
                    )
                )
            ) is not None
            and timestamp >= cutoff
        ]

        production_litres = sum(
            max(
                0.0,
                float(
                    row.total_yield or 0.0
                ),
            )
            for row in milk
            if str(
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
            }
        )

        expenses = [
            row
            for row in finance
            if classifier.is_expense(row)
        ]

        income = [
            row
            for row in finance
            if classifier.is_income(row)
        ]

        non_operating = [
            row
            for row in finance
            if classifier.is_cash_movement_only(row)
        ]

        unclassified = [
            row
            for row in finance
            if not classifier.is_known_type(row)
        ]

        by_category: dict[str, float] = defaultdict(float)

        for row in expenses:
            category = str(
                row.category or "UNCLASSIFIED"
            ).strip().upper()

            by_category[category] += float(
                row.amount or 0.0
            )

        total_expenses = sum(
            by_category.values()
        )

        covered_domains: dict[str, float] = {}

        for domain, categories in (
            self.COST_DOMAIN_CATEGORIES.items()
        ):
            covered_domains[domain] = round(
                sum(
                    value
                    for category, value
                    in by_category.items()
                    if category in categories
                ),
                2,
            )

        missing_domains = [
            domain
            for domain, amount
            in covered_domains.items()
            if amount <= 0.0
        ]

        covered_cost_domains = [
            domain
            for domain, amount
            in covered_domains.items()
            if amount > 0.0
        ]

        milk_revenue = sum(
            float(row.amount or 0.0)
            for row in income
            if str(
                row.category or ""
            ).strip().upper()
            in self.MILK_REVENUE_CATEGORIES
        )

        return {
            "period_days": days,
            "from": cutoff.isoformat(),
            "to": now.isoformat(),
            "data_status": "LIVE_PERSISTED_DATA",
            "milk_litres": round(
                production_litres,
                3,
            ),
            "expense_count": len(expenses),
            "income_count": len(income),
            "non_operating_outflow_count": len(
                non_operating
            ),
            "non_operating_outflow_total": round(
                sum(
                    float(row.amount or 0.0)
                    for row in non_operating
                ),
                2,
            ),
            "unclassified_transaction_count": len(
                unclassified
            ),
            "total_recorded_operating_expense": round(
                total_expenses,
                2,
            ),
            "cost_per_litre": (
                round(
                    total_expenses / production_litres,
                    4,
                )
                if production_litres
                else None
            ),
            "expense_by_category": {
                key: round(
                    value,
                    2,
                )
                for key, value
                in sorted(
                    by_category.items()
                )
            },
            "cost_domain_amounts": covered_domains,
            "covered_cost_domains": covered_cost_domains,
            "missing_cost_domains": missing_domains,
            "cost_data_completeness": (
                "COMPLETE"
                if production_litres
                and not missing_domains
                else "PARTIAL"
                if production_litres
                and covered_cost_domains
                else "INSUFFICIENT"
            ),
            "milk_revenue": (
                round(
                    milk_revenue,
                    2,
                )
                if milk_revenue
                else None
            ),
            "revenue_per_litre": (
                round(
                    milk_revenue / production_litres,
                    4,
                )
                if milk_revenue
                and production_litres
                else None
            ),
            "margin_after_recorded_operating_cost": (
                round(
                    milk_revenue - total_expenses,
                    2,
                )
                if milk_revenue
                else None
            ),
            "margin_per_litre": (
                round(
                    (
                        milk_revenue
                        - total_expenses
                    )
                    / production_litres,
                    4,
                )
                if milk_revenue
                and production_litres
                else None
            ),
            "quality": (
                "COMPLETE_FOR_DECLARED_COST_DOMAINS"
                if production_litres
                and not missing_domains
                else "PARTIAL_PERSISTED_COST_COVERAGE"
                if production_litres
                and covered_cost_domains
                else "INSUFFICIENT_PERSISTED_COST_OR_PRODUCTION_DATA"
            ),
        }
