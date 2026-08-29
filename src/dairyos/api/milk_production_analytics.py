from __future__ import annotations

from datetime import date, datetime, time

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
    resolve_period_range,
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
    period_days: int = Query(default=30, ge=1),
):
    if period_days not in {7, 15, 30} and period_days not in SUPPORTED_PERIOD_DAYS.values():
        raise HTTPException(status_code=422, detail="Unsupported period_days. Supported production periods include 7, 15 and 30 days.")

    service = MilkProductionTrendIntelligenceService()
    target_date = production_date or service._get_factory().app_settings if False else (production_date or __import__("dairyos.farm.settings.services.operational_date_authority", fromlist=["OperationalDateAuthority"]).OperationalDateAuthority().current_date())

    rf = RepositoryFactory.create()
    try:
        if period_days == 15:
            start_date, end_date = resolve_period_range(
                period="custom",
                start_date=target_date.replace() - __import__("datetime").timedelta(days=14),
                end_date=target_date,
                anchor_date=target_date,
            )
            trend = service.get_trend_analysis(
                period="custom",
                start_date=start_date,
                end_date=end_date,
                anchor_date=target_date,
                factory=rf,
            )
            trend["period_days"] = 15
            trend["period"] = "15d"
        else:
            trend = service.generate(
                as_of_date=production_date,
                period_days=period_days,
                repository_factory=rf,
            )

        findings = rf.operational_findings().get_open_by_module("MILK")
        individual_declines = [
            {
                "finding_id": finding.finding_id,
                "animal_id": finding.subject_id,
                "severity": finding.severity,
                "title": finding.title,
                "detail": finding.detail,
                "status": finding.status,
                "route": finding.route,
                "observation_count": finding.observation_count,
            }
            for finding in findings
            if finding.subject_type == "ANIMAL"
            and finding.dedupe_key
            and finding.dedupe_key.startswith("MILK_DAILY_DROP:")
            and finding.severity in {"HIGH", "CRITICAL"}
        ]

        # Production extremes are derived from complete, schedule-governed
        # animal-day snapshots using the same trend intelligence service.
        animals = service._eligible_animals(rf)
        histories = service._animal_histories(rf, animals)
        snapshots = []
        for animal in animals:
            snapshot = service._daily_animal_snapshot(
                rf.milk().get_all(),
                animal,
                histories.get(str(animal.animal_id), []),
                target_date,
            )
            if snapshot and snapshot.get("complete"):
                snapshots.append(snapshot)

        snapshots.sort(key=lambda item: item["total_litres"])
        extremes = {
            "highest": snapshots[-1] if snapshots else None,
            "lowest": snapshots[0] if snapshots else None,
            "population_count": len(snapshots),
            "data_status": "LIVE_PERSISTED_DATA" if snapshots else "NO_DATA",
        }

        result = trend.summary()
        result.update({
            "period_options_days": [7, 15, 30],
            "individual_decline_alert_count": len(individual_declines),
            "individual_decline_alerts": individual_declines,
            "production_extremes": extremes,
        })
        return result
    finally:
        rf.close()


# AUDIT-FIX [WIRING-ROUTER-01]: Removed duplicate GET /farm/milk/reconciliation route.
# The authoritative endpoint is registered in milk_traceability.py with full query-param
# support and operational date fallback, resolving FastAPI duplicate Operation ID warning.


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
        from dairyos.core.time_utils import utcnow
        disposition.updated_at = utcnow()

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
