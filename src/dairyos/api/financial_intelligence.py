"""Financial intelligence derived from persisted farm transactions and milk."""
from __future__ import annotations

from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, Query

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.finance.profitability.services.cost_of_production_service import CostOfProductionService

router = APIRouter(prefix="/farm/finance", tags=["financial-intelligence"])


@router.get("/cost-of-production")
def cost_of_production(days: int = Query(default=30, ge=1, le=366)):
    factory = RepositoryFactory.create()
    try:
        service = CostOfProductionService()
        return service.evaluate(
            factory.milk().get_all(),
            factory.finance().get_all(),
            days=days,
        )
    finally:
        factory.close()


@router.get("/reconciliation")
def reconciliation(period: str = Query(default="monthly", pattern="^(monthly|quarterly|yearly)$")):
    now = datetime.utcnow()
    if period == "monthly":
        start = datetime(now.year, now.month, 1)
    elif period == "quarterly":
        month = ((now.month - 1) // 3) * 3 + 1
        start = datetime(now.year, month, 1)
    else:
        start = datetime(now.year, 1, 1)
    factory = RepositoryFactory.create()
    try:
        records = [x for x in factory.finance().get_all() if x.transaction_date >= start]
        income = sum(float(x.amount or 0) for x in records if classifier.is_income(x))
        expenses = sum(float(x.amount or 0) for x in records if classifier.is_expense(x))
        # Real money out that is not a farm cost -- owner drawings and loan
        # repayments. Reported separately rather than folded into expenses
        # (which would inflate cost per litre) or dropped entirely, which is
        # what happened before 2026-08-14: these types matched neither bucket
        # and contributed nothing to any total.
        non_operating = sum(
            float(x.amount or 0) for x in records if classifier.is_cash_movement_only(x)
        )
        unclassified = [x for x in records if not classifier.is_known_type(x)]
        return {
            "period": period,
            "from": start.isoformat(),
            "to": now.isoformat(),
            "data_status": "LIVE_PERSISTED",
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "net_movement": round(income - expenses, 2),
            "non_operating_outflows": round(non_operating, 2),
            "net_cash_movement": round(income - expenses - non_operating, 2),
            "transaction_count": len(records),
            # An unrecognised transaction type must never vanish into a total
            # that then looks complete.
            "unclassified_transaction_count": len(unclassified),
            "unclassified_transaction_types": sorted(
                {
                    classifier.normalize_transaction_type(x.transaction_type)
                    for x in unclassified
                }
            ),
            "accounting_note": (
                "net_movement is operating income less operating expenses. Owner "
                "withdrawals and loan repayments are real cash outflows but not farm "
                "costs, so they are reported as non_operating_outflows and excluded "
                "from expenses; net_cash_movement includes them. Account-level "
                "cash/bank balances are reported only when persisted account data "
                "exists; this endpoint never infers account location from "
                "transaction text."
            ),
        }
    finally:
        factory.close()
