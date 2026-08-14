from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
    VALID_DISPOSITIONS,
)
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
    SUPPORTED_PERIOD_DAYS,
)


router = APIRouter(prefix="/farm/milk", tags=["Milk Production Analytics"])


class MilkDispositionRequest(BaseModel):
    production_date: date
    disposition_type: str
    quantity_litres: float = Field(gt=0)
    sale_id: str | None = None
    counterparty: str | None = None
    selling_price_per_litre: float | None = Field(default=None, ge=0)
    notes: str | None = None
    recorded_by: str = Field(default="UI Operator", min_length=1)


class MilkReceiptRequest(BaseModel):
    amount: float = Field(gt=0)
    payment_method: str | None = None
    counterparty: str | None = None
    notes: str | None = None
    received_on: date | None = None
    recorded_by: str = Field(default="UI Operator", min_length=1)


@router.get("/analytics")
def milk_analytics(
    production_date: date | None = None,
    period_days: int = Query(default=30, enum=list(SUPPORTED_PERIOD_DAYS)),
):
    trend = MilkProductionTrendIntelligenceService().generate(
        as_of_date=production_date,
        period_days=period_days,
    )
    return trend.summary()


@router.get("/reconciliation")
def milk_reconciliation(production_date: date):
    return MilkReconciliationService().reconcile(production_date)


@router.get("/dispositions")
def list_milk_dispositions(production_date: date | None = None):
    rf = RepositoryFactory.create()
    try:
        repo = rf.milk_dispositions()
        rows = repo.get_by_date(production_date) if production_date else repo.get_all()
        return {
            "dispositions": [
                {
                    "id": row.id,
                    "production_date": row.production_date.isoformat(),
                    "disposition_type": row.disposition_type,
                    "quantity_litres": row.quantity_litres,
                    "sale_id": row.sale_id,
                    "counterparty": row.counterparty,
                    "selling_price_per_litre": row.selling_price_per_litre,
                    "amount_due": row.amount_due,
                    "amount_received": row.amount_received,
                    "receivable_outstanding": row.receivable_outstanding,
                    "notes": row.notes,
                    "recorded_by": row.recorded_by,
                }
                for row in rows
            ]
        }
    finally:
        rf.close()


@router.post("/dispositions")
def record_milk_disposition(payload: MilkDispositionRequest):
    if payload.disposition_type.strip().upper() not in VALID_DISPOSITIONS:
        raise HTTPException(status_code=422, detail="Unknown milk disposition type.")
    try:
        row = MilkReconciliationService().record_disposition(
            production_date=payload.production_date,
            disposition_type=payload.disposition_type,
            quantity_litres=payload.quantity_litres,
            sale_id=payload.sale_id,
            counterparty=payload.counterparty,
            selling_price_per_litre=payload.selling_price_per_litre,
            notes=payload.notes,
            recorded_by=payload.recorded_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "id": row.id,
        "production_date": row.production_date.isoformat(),
        "disposition_type": row.disposition_type,
        "quantity_litres": row.quantity_litres,
        "sale_id": row.sale_id,
        "amount_due": row.amount_due,
        "amount_received": row.amount_received,
        "receivable_outstanding": row.receivable_outstanding,
    }


@router.post("/sales/{sale_id}/receipt")
def record_milk_sale_receipt(sale_id: str, payload: MilkReceiptRequest):
    rf = RepositoryFactory.create()
    try:
        disposition = rf.milk_dispositions().get_by_sale_id(sale_id)
        if disposition is None:
            raise HTTPException(status_code=404, detail=f"Unknown milk sale {sale_id}.")
        if str(disposition.disposition_type).upper() != "SOLD":
            raise HTTPException(status_code=422, detail="Only SOLD milk dispositions can receive payment.")

        outstanding = disposition.receivable_outstanding
        if payload.amount > outstanding + 0.01:
            raise HTTPException(
                status_code=422,
                detail=f"Receipt exceeds outstanding receivable by {payload.amount - outstanding:.2f}.",
            )

        disposition.amount_received = float(disposition.amount_received or 0.0) + payload.amount
        disposition.updated_at = __import__("dairyos.core.time_utils", fromlist=["utcnow"]).utcnow()

        transaction = FinancialTransaction(
            transaction_type="RECEIPT",
            category="MILK_SALES",
            amount=payload.amount,
            reference=sale_id,
            payment_method=payload.payment_method,
            counterparty=payload.counterparty or disposition.counterparty,
            notes=payload.notes,
            status="RECORDED",
            currency="PKR",
            milk_sale_id=sale_id,
        )
        if payload.received_on is not None:
            from datetime import datetime, time
            transaction.transaction_date = datetime.combine(payload.received_on, time.min)

        rf.session.add(transaction)
        rf.session.commit()
        rf.session.refresh(disposition)
        rf.session.refresh(transaction)

        return {
            "sale_id": sale_id,
            "receipt_amount": payload.amount,
            "amount_received": disposition.amount_received,
            "receivable_outstanding": disposition.receivable_outstanding,
            "financial_transaction_id": transaction.id,
        }
    finally:
        rf.close()
