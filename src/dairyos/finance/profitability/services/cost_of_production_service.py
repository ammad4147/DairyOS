from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta


class CostOfProductionService:
    """Derive cost-of-production metrics only from persisted farm records.

    The service never substitutes assumptions for missing persisted costs. Cost
    coverage is explicit so a partial ledger cannot be presented as a complete
    dairy cost model.
    """

    MILK_REVENUE_CATEGORIES = {
        "MILK",
        "MILK SALE",
        "MILK SALES",
        "DAIRY SALES",
    }

    COST_DOMAIN_CATEGORIES = {
        "FEED": {"FEED", "FEEDING"},
        "LABOUR": {"LABOUR", "LABOR", "WORKFORCE", "WAGES", "SALARY", "SALARIES"},
        "HEALTH": {"VETERINARY", "VET", "HEALTH", "MEDICINE", "TREATMENT"},
        "BREEDING": {"BREEDING", "REPRODUCTION", "SEMEN"},
        "UTILITIES": {"UTILITIES", "ELECTRICITY", "WATER", "FUEL"},
        "EQUIPMENT": {"EQUIPMENT", "REPAIRS", "MAINTENANCE", "MACHINERY"},
        "OTHER_OPERATING": {"OTHER", "GENERAL", "OPERATING", "OTHER OPERATING"},
    }

    def evaluate(self, milk_records, financial_records, days: int = 30, now: datetime | None = None):
        if days < 1:
            raise ValueError("days must be positive")

        now = now or datetime.utcnow()
        cutoff = now - timedelta(days=days)

        milk = [row for row in milk_records if row.production_date >= cutoff]
        finance = [row for row in financial_records if row.transaction_date >= cutoff]

        production_litres = sum(
            max(0.0, float(row.total_yield or 0.0))
            for row in milk
            if str(row.status or "RECORDED").upper() != "WITHHELD"
        )

        expenses = [row for row in finance if str(row.transaction_type).upper() == "EXPENSE"]
        income = [row for row in finance if str(row.transaction_type).upper() == "INCOME"]

        by_category: dict[str, float] = defaultdict(float)
        for row in expenses:
            category = str(row.category or "UNCLASSIFIED").strip().upper()
            by_category[category] += float(row.amount or 0.0)

        total_expenses = sum(by_category.values())

        covered_domains: dict[str, float] = {}
        for domain, categories in self.COST_DOMAIN_CATEGORIES.items():
            covered_domains[domain] = round(
                sum(value for category, value in by_category.items() if category in categories),
                2,
            )

        missing_domains = [domain for domain, amount in covered_domains.items() if amount <= 0.0]
        covered_cost_domains = [domain for domain, amount in covered_domains.items() if amount > 0.0]

        milk_revenue = sum(
            float(row.amount or 0.0)
            for row in income
            if row.milk_sale_id is not None
            or str(row.category or "").strip().upper() in self.MILK_REVENUE_CATEGORIES
        )

        result = {
            "period_days": days,
            "from": cutoff.isoformat(),
            "to": now.isoformat(),
            "data_status": "LIVE_PERSISTED_DATA",
            "milk_litres": round(production_litres, 3),
            "expense_count": len(expenses),
            "income_count": len(income),
            "total_recorded_operating_expense": round(total_expenses, 2),
            "cost_per_litre": round(total_expenses / production_litres, 4) if production_litres else None,
            "expense_by_category": {key: round(value, 2) for key, value in sorted(by_category.items())},
            "cost_domain_amounts": covered_domains,
            "covered_cost_domains": covered_cost_domains,
            "missing_cost_domains": missing_domains,
            "cost_data_completeness": (
                "COMPLETE"
                if production_litres and not missing_domains
                else "PARTIAL"
                if production_litres and covered_cost_domains
                else "INSUFFICIENT"
            ),
            "milk_revenue": round(milk_revenue, 2) if milk_revenue else None,
            "revenue_per_litre": round(milk_revenue / production_litres, 4)
            if milk_revenue and production_litres else None,
            "margin_after_recorded_operating_cost": round(milk_revenue - total_expenses, 2)
            if milk_revenue else None,
            "margin_per_litre": round((milk_revenue - total_expenses) / production_litres, 4)
            if milk_revenue and production_litres else None,
            "quality": (
                "COMPLETE_FOR_DECLARED_COST_DOMAINS"
                if production_litres and not missing_domains
                else "PARTIAL_PERSISTED_COST_COVERAGE"
                if production_litres and covered_cost_domains
                else "INSUFFICIENT_PERSISTED_COST_OR_PRODUCTION_DATA"
            ),
        }
        return result
