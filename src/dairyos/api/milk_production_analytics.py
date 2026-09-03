from __future__ import annotations

from datetime import date, datetime, time, timedelta

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
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
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


def _production_extremes(
    *,
    service: MilkProductionTrendIntelligenceService,
    records,
    animals,
    histories,
    target_date: date,
) -> dict:
    """Return latest actually-recorded animal production extremes.

    The old surface required a complete animal-day before showing anything,
    which made the panel blank during ordinary live operations. Extremes are
    descriptive, not a completed-day comparison, so valid partial production
    is sufficient. If the selected day has no recorded milk yet, fall back to
    the most recent recorded day in the prior week.
    """

    selected_date = None
    snapshots = []

    for offset in range(0, 7):
        candidate_date = target_date - timedelta(days=offset)
        candidate = []

        for animal in animals:
            animal_id = str(getattr(animal, "animal_id", ""))
            snapshot = service._daily_animal_snapshot(
                records,
                animal,
                histories.get(animal_id, []),
                candidate_date,
            )
            if snapshot and float(snapshot.get("total_litres") or 0.0) > 0:
                candidate.append(snapshot)

        if candidate:
            selected_date = candidate_date
            snapshots = candidate
            break

    snapshots.sort(key=lambda item: float(item.get("total_litres") or 0.0))

    # Production Extremes must be mutually exclusive. The Dashboard
    # displays whole litres, so classification uses the same displayed
    # litre band rather than allowing visually identical values to
    # appear in both Highest and Lowest.
    def displayed_litre_band(item) -> int:
        litres = float(item.get("total_litres") or 0.0)
        return int(litres + 0.5)

    yield_bands = sorted(
        {displayed_litre_band(item) for item in snapshots}
    )

    lowest_bands: set[int] = set()
    highest_bands: set[int] = set()

    if len(yield_bands) > 1:
        split = len(yield_bands) // 2

        if len(yield_bands) % 2:
            # Odd number of distinct production bands:
            # the middle band is neutral and appears in neither list.
            lowest_bands = set(yield_bands[:split])
            highest_bands = set(yield_bands[split + 1:])
        else:
            # Even number of distinct production bands:
            # split cleanly between lower and upper halves.
            lowest_bands = set(yield_bands[:split])
            highest_bands = set(yield_bands[split:])

    highest = [
        item
        for item in reversed(snapshots)
        if displayed_litre_band(item) in highest_bands
    ]
    lowest = [
        item
        for item in snapshots
        if displayed_litre_band(item) in lowest_bands
    ]

    return {
        "highest": highest,
        "lowest": lowest,
        "population_count": len(snapshots),
        "production_date": selected_date.isoformat() if selected_date else None,
        "data_status": "LIVE_PERSISTED_DATA" if snapshots else "NO_DATA",
    }


def _yield_drop_watchlist(
    *,
    service: MilkProductionTrendIntelligenceService,
    records,
    animals,
    histories,
    target_date: date,
    lookback_days: int,
) -> list[dict]:
    """Derive yield-drop alerts directly from governed complete animal-days."""

    watchlist: list[dict] = []
    window = max(7, min(int(lookback_days), 30))

    for animal in animals:
        animal_id = str(getattr(animal, "animal_id", ""))
        complete: list[dict] = []

        for offset in range(window):
            candidate_date = target_date - timedelta(days=offset)
            snapshot = service._daily_animal_snapshot(
                records,
                animal,
                histories.get(animal_id, []),
                candidate_date,
            )
            if snapshot and snapshot.get("complete"):
                complete.append(snapshot)
                if len(complete) == 2:
                    break

        if len(complete) < 2:
            continue

        current, previous = complete[0], complete[1]
        current_litres = float(current.get("total_litres") or 0.0)
        previous_litres = float(previous.get("total_litres") or 0.0)

        if previous_litres <= 0 or current_litres >= previous_litres:
            continue

        drop_percentage = ((previous_litres - current_litres) / previous_litres) * 100.0
        if drop_percentage < 15.0:
            continue

        severity = "CRITICAL" if drop_percentage >= 30.0 else "HIGH"
        watchlist.append(
            {
                "finding_id": None,
                "animal_id": animal_id,
                "severity": severity,
                "title": f"Milk yield drop: {animal_id}",
                "detail": (
                    f"{previous_litres:.1f} L on {previous['date']} → "
                    f"{current_litres:.1f} L on {current['date']} "
                    f"({drop_percentage:.1f}% decline)."
                ),
                "status": "DERIVED_LIVE",
                "route": "/farm/milk",
                "observation_count": 2,
                "current_date": current["date"],
                "previous_date": previous["date"],
                "current_litres": round(current_litres, 2),
                "previous_litres": round(previous_litres, 2),
                "drop_percentage": round(drop_percentage, 1),
            }
        )

    watchlist.sort(
        key=lambda item: (item["drop_percentage"], item["animal_id"]),
        reverse=True,
    )
    return watchlist


@router.get("/analytics")
def milk_analytics(
    production_date: date | None = None,
    period_days: int = Query(default=30, ge=1),
):
    supported_periods = {7, 15, 30} | set(SUPPORTED_PERIOD_DAYS.values())
    if period_days not in supported_periods:
        raise HTTPException(
            status_code=422,
            detail="Unsupported period_days. Supported production periods include 7, 15 and 30 days.",
        )

    target_date = production_date or OperationalDateAuthority().current_date()
    rf = RepositoryFactory.create()

    try:
        service = MilkProductionTrendIntelligenceService(repository_factory=rf)
        if period_days == 15:
            trend = service.get_trend_analysis(
                period="custom",
                start_date=target_date - timedelta(days=14),
                end_date=target_date,
                anchor_date=target_date,
                factory=rf,
            )
            trend["period_days"] = 15
            trend["period"] = "15d"
        else:
            trend = service.generate(as_of_date=target_date, period_days=period_days)

        animals = service._eligible_animals(rf)
        histories = service._animal_histories(rf, animals)
        records = rf.milk().get_all()

        individual_declines = _yield_drop_watchlist(
            service=service,
            records=records,
            animals=animals,
            histories=histories,
            target_date=target_date,
            lookback_days=period_days,
        )
        extremes = _production_extremes(
            service=service,
            records=records,
            animals=animals,
            histories=histories,
            target_date=target_date,
        )

        result = dict(trend)
        result.update(
            {
                "period_options_days": [7, 15, 30],
                "individual_decline_alert_count": len(individual_declines),
                "individual_decline_alerts": individual_declines,
                "production_extremes": extremes,
            }
        )
        return result
    finally:
        rf.close()


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
