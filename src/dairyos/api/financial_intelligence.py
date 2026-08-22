"""Financial intelligence derived from persisted farm transactions and milk."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.finance.profitability.services.feed_opex_cost_service import FeedOpexCostService
from dairyos.core.time_utils import utcnow

router = APIRouter(prefix="/farm/finance", tags=["financial-intelligence"])


@router.get("/cost-of-production")
def cost_of_production(days: int = Query(default=30, ge=1, le=366)):
    factory = RepositoryFactory.create()
    try:
        return FeedOpexCostService().evaluate(
            factory.milk().get_all(),
            factory.finance().get_all(),
            days=days,
        )
    finally:
        factory.close()


@router.get("/reconciliation")
def reconciliation(period: str = Query(default="monthly", pattern="^(monthly|quarterly|yearly)$")):
    now = utcnow()
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
        active_records = [x for x in records if classifier.is_active(x)]
        income = sum(float(x.amount or 0) for x in active_records if classifier.is_income(x))
        expenses = sum(float(x.amount or 0) for x in active_records if classifier.is_expense(x))
        non_operating = sum(float(x.amount or 0) for x in active_records if classifier.is_cash_movement_only(x))
        unclassified = [x for x in active_records if not classifier.is_known_type(x)]
        feed = sum(float(x.amount or 0) for x in active_records if classifier.is_expense(x) and str(getattr(x, "master_category", "") or "").upper() == "FEED")
        opex = sum(float(x.amount or 0) for x in active_records if classifier.is_expense(x) and str(getattr(x, "master_category", "") or "").upper() == "OPEX")
        return {
            "period": period,
            "from": start.isoformat(),
            "to": now.isoformat(),
            "data_status": "LIVE_PERSISTED",
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "feed_cost": round(feed, 2),
            "opex": round(opex, 2),
            "total_operating_cost": round(feed + opex, 2),
            "net_movement": round(income - expenses, 2),
            "non_operating_outflows": round(non_operating, 2),
            "net_cash_movement": round(income - expenses - non_operating, 2),
            "transaction_count": len(records),
            "active_transaction_count": len(active_records),
            "unclassified_transaction_count": len(unclassified),
            "unclassified_transaction_types": sorted({classifier.normalize_transaction_type(x.transaction_type) for x in unclassified}),
            "accounting_note": (
                "net_movement is operating income less operating expenses. Owner withdrawals and loan repayments are real cash outflows but not farm costs; net_cash_movement includes them."
            ),
        }
    finally:
        factory.close()
