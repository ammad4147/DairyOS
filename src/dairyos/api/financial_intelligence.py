"""Financial intelligence derived from persisted farm transactions and milk."""
from __future__ import annotations

from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import APIRouter, Query

from dairyos.data.repositories.repository_factory import RepositoryFactory
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
        income = sum(float(x.amount or 0) for x in records if x.transaction_type == "INCOME")
        expenses = sum(float(x.amount or 0) for x in records if x.transaction_type == "EXPENSE")
        return {
            "period": period,
            "from": start.isoformat(),
            "to": now.isoformat(),
            "data_status": "LIVE_PERSISTED",
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "net_movement": round(income - expenses, 2),
            "transaction_count": len(records),
            "accounting_note": "Account-level cash/bank balances are reported only when persisted account data exists; this endpoint never infers account location from transaction text.",
        }
    finally:
        factory.close()
