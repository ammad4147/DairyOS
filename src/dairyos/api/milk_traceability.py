"""Persisted Milk register, reconciliation and animal traceability API."""
from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.api.auth import get_optional_current_user
from dairyos.api.dependencies import get_container
from dairyos.api.operational_write import operational_write
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.milk_production_correction import (
    MilkProductionCorrection,
)
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.herd.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)
from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)
from dairyos.farm.production.services.milk_inventory_capacity_service import (
    overall_saleable_capacity,
)
from dairyos.farm.production.services.missed_milking_control_service import (
    MissedMilkingControlService,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from dairyos.core.time_utils import utcnow


# Schema preparation is migration-gate owned. Importing this router is
# intentionally database-schema read-only.

router = APIRouter(prefix="/farm/milk", tags=["Milk"])


class ProductionPatch(BaseModel):
    request_id: str | None = Field(default=None, min_length=1, max_length=128)
    production_date: date | None = None
    morning_yield: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    afternoon_yield: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    evening_yield: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    notes: str | None = None
    correction_reason: str | None = Field(default=None, max_length=500)
    operator: str | None = Field(default=None, min_length=1, max_length=128)


class DispositionCreate(BaseModel):
    production_date: date
    disposition_type: str
    quantity_litres: float = Field(gt=0)
    sale_id: str | None = None
    counterparty: str | None = None
    selling_price_per_litre: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class DispositionPatch(BaseModel):
    production_date: date | None = None
    quantity_litres: float | None = Field(default=None, gt=0)
    counterparty: str | None = None
    selling_price_per_litre: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class VoidRequest(BaseModel):
    request_id: str | None = Field(default=None, min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=500)
    operator: str | None = Field(default=None, min_length=1, max_length=128)


def _operator(
    current_user: dict[str, Any] | None,
    fallback: str | None = None,
) -> str:
    return str(current_user["sub"]) if current_user else str(fallback or "API")


def _meaningful_correction_reason(
    supplied: str | None,
    notes: str | None = None,
) -> str:
    for value in (supplied, notes):
        text_value = str(value or "").strip()
        if text_value:
            return text_value
    raise HTTPException(
        status_code=422,
        detail="A meaningful correction reason is required.",
    )


def _correction_payload(
    *,
    production_id: int,
    action: str,
    reason: str,
    operator: str,
    before: dict[str, Any],
    after: dict[str, Any],
    source_request_id: str | None,
) -> dict[str, Any]:
    return {
        "production_id": production_id,
        "action": action,
        "reason": reason,
        "operator": operator,
        "before": before,
        "after": after,
        "source_request_id": source_request_id,
    }


def _record_milk_correction(
    *,
    container,
    production_id: int,
    action: str,
    reason: str,
    operator: str,
    before: dict[str, Any],
    after: dict[str, Any],
    source_request_id: str | None,
) -> MilkProductionCorrection:
    factory = container.repository_factory
    correction = MilkProductionCorrection(
        production_id=production_id,
        action=action,
        reason=reason,
        operator=operator,
        before_json=before,
        after_json=after,
        source_request_id=source_request_id,
    )
    factory.session.add(correction)
    factory.session.flush()

    gateway = getattr(container, "input_gateway", None)
    if gateway is not None:
        gateway.record(
            input_type="milk_production_correction",
            payload=_correction_payload(
                production_id=production_id,
                action=action,
                reason=reason,
                operator=operator,
                before=before,
                after=after,
                source_request_id=source_request_id,
            ),
            actor=operator,
        )

    return correction


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _production_payload(record: MilkProduction) -> dict[str, Any]:
    return {
        "id": record.id,
        "animal_id": record.animal_id,
        "production_date": _iso(record.production_date),
        "recorded_at": _iso(record.recorded_at),
        "milking_session": record.milking_session,
        "session_ledger": bool(record.session_ledger),
        "morning_yield": record.morning_yield,
        "afternoon_yield": record.afternoon_yield,
        "evening_yield": record.evening_yield,
        "total_yield": record.total_yield,
        "status": record.status,
        "notes": record.notes,
    }


def _disposition_payload(item: MilkDisposition) -> dict[str, Any]:
    return {
        "id": item.id,
        "production_date": _iso(item.production_date),
        "disposition_type": item.disposition_type,
        "quantity_litres": item.quantity_litres,
        "sale_id": item.sale_id,
        "counterparty": item.counterparty,
        "selling_price_per_litre": item.selling_price_per_litre,
        "amount_due": item.amount_due,
        "amount_received": item.amount_received,
        "receivable_outstanding": item.receivable_outstanding,
        "notes": item.notes,
        "recorded_by": item.recorded_by,
        "status": item.status,
        "created_at": _iso(item.created_at),
        "updated_at": _iso(item.updated_at),
    }


def _production_date(value: date | None) -> date:
    return value or OperationalDateAuthority().current_date()


def _append_void_note(existing: str | None, reason: str, snapshot: dict[str, Any]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, default=str)
    prefix = (existing or "").strip()
    if prefix:
        prefix += "\n"
    return (
        f"{prefix}VOIDED_AT={utcnow().isoformat()} "
        f"REASON={reason}\nVOID_SNAPSHOT={payload}"
    )


def _primary_finance_sale_for_disposition(
    session,
    item: MilkDisposition,
    *,
    lock: bool = False,
) -> FinancialTransaction | None:
    """Return the primary Finance sale for a FIN-{id} Milk sale identity."""
    sale_id = str(item.sale_id or "").strip()

    if not sale_id.startswith("FIN-"):
        return None

    raw_id = sale_id[4:]
    if not raw_id.isdigit():
        raise HTTPException(
            status_code=409,
            detail=f"Malformed Finance-linked milk sale identity: {sale_id}.",
        )

    query = session.query(FinancialTransaction).filter(
        FinancialTransaction.id == int(raw_id),
    )

    if lock:
        query = query.with_for_update()

    transaction = query.first()

    if transaction is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Milk sale references a missing primary Finance transaction "
                f"({sale_id})."
            ),
        )

    if str(transaction.category or "").upper() != "MILK_SALES":
        raise HTTPException(
            status_code=409,
            detail=(
                f"{sale_id} does not reference a MILK_SALES Finance transaction."
            ),
        )

    return transaction


def _active_disposition_sum(session, production_date: date, exclude_id: int | None = None) -> float:
    query = session.query(MilkDisposition).filter(
        MilkDisposition.production_date == production_date,
        MilkDisposition.status != "VOID",
    )
    if exclude_id is not None:
        query = query.filter(MilkDisposition.id != exclude_id)
    return sum(float(row.quantity_litres or 0.0) for row in query.all())


@router.post("/missed-sessions/reconcile")
def reconcile_missed_milking_sessions(
    lookback_days: int = Query(default=31, ge=1, le=90),
    container=Depends(get_container),
):
    """Persist missed per-animal milking controls for completed dates only."""
    return MissedMilkingControlService(
        container.repository_factory
    ).reconcile(lookback_days=lookback_days)


@router.get("/missed-sessions")
def inspect_missed_milking_sessions(
    lookback_days: int = Query(default=31, ge=1, le=90),
    container=Depends(get_container),
):
    """Return the current missed-milking control without persisting changes."""
    return MissedMilkingControlService(
        container.repository_factory
    ).inspect(lookback_days=lookback_days)


@router.get("/{animal_id}/traceability")
def animal_milk_traceability(animal_id: str, container=Depends(get_container)):
    animal = container.animal_repository.get_by_animal_id(animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")

    milk_records = [
        record
        for record in container.milk_repository.get_all()
        if str(record.animal_id) == animal_id
    ]

    operational_events = []
    for event in container.operational_event_repository.get_all():
        description = str(getattr(event, "description", ""))
        if "milk_production" in description and (
            f"entity_id={animal_id}" in description
            or f"animal_id={animal_id}" in description
        ):
            operational_events.append(
                {
                    "id": getattr(event, "id", None),
                    "event_type": getattr(event, "event_type", None),
                    "source": getattr(event, "source", None),
                    "description": description,
                    "created_at": _iso(getattr(event, "created_at", None)),
                }
            )

    total_litres = sum(
        float(record.total_yield or 0)
        for record in milk_records
        if str(record.status).upper() != "VOID"
    )
    return {
        "data_status": "LIVE_PERSISTED",
        "animal": {
            "animal_id": animal.animal_id,
            "ear_tag": animal.ear_tag,
            "breed": animal.breed,
            "lifecycle_status": animal.lifecycle_status,
        },
        "milk_records": [_production_payload(record) for record in milk_records],
        "operational_trace": operational_events,
        "record_count": len(milk_records),
        "total_litres": total_litres,
        "traceability_complete": all(
            str(record.animal_id) == animal_id for record in milk_records
        ),
    }


@router.get("/ledger")
def milk_ledger(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    container=Depends(get_container),
):
    start = start_date or date.min
    end = end_date or date.max
    if start > end:
        raise HTTPException(status_code=422, detail="start_date cannot be after end_date")

    factory = RepositoryFactory.create(session=container.repository_factory.session)
    try:
        productions = [
            row
            for row in factory.milk().get_all()
            if start <= row.production_date.date() <= end
        ]
        dispositions = [
            row
            for row in factory.milk_dispositions().get_all()
            if start <= row.production_date <= end
        ]
        return {
            "data_status": "LIVE_PERSISTED",
            "production": sorted(
                [_production_payload(row) for row in productions],
                key=lambda row: (row["production_date"], row["animal_id"], row["id"]),
            ),
            "dispositions": sorted(
                [_disposition_payload(row) for row in dispositions],
                key=lambda row: (row["production_date"], row["id"]),
            ),
        }
    finally:
        factory.close()


@router.get("/reconciliation")
def milk_reconciliation(
    production_date: date | None = Query(default=None),
):
    target = _production_date(production_date)
    return MilkReconciliationService().reconcile(target, raise_finding=False)


@router.get("/capacity")
def milk_capacity(
    through_date: date | None = Query(default=None),
    container=Depends(get_container),
):
    target = _production_date(through_date)
    return overall_saleable_capacity(
        target,
        factory=container.repository_factory,
    )


@router.patch("/production/{record_id}")
@operational_write
def update_milk_production(
    record_id: int,
    patch: ProductionPatch,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    factory = container.repository_factory
    session = factory.session
    record = (
        session.query(MilkProduction)
        .filter(MilkProduction.id == record_id)
        .with_for_update()
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Milk production record not found")
    if str(record.status).upper() == "VOID":
        raise HTTPException(status_code=409, detail="VOID milk production cannot be edited")

    reason = _meaningful_correction_reason(
        patch.correction_reason,
    )
    operator = _operator(current_user, patch.operator)
    original_date = (
        record.production_date.date()
        if hasattr(record.production_date, "date")
        else record.production_date
    )
    new_date = patch.production_date or original_date
    today = OperationalDateAuthority(
        repository_factory=factory,
    ).current_date()
    if new_date > today:
        raise HTTPException(
            status_code=422,
            detail="Milk production cannot be corrected to a future date.",
        )

    before = _production_payload(record)

    if record.session_ledger:
        animal = factory.animal().get_by_animal_id(record.animal_id)
        if animal is None:
            raise HTTPException(status_code=409, detail="Animal no longer exists")
        expected = AnimalMilkingScheduleService().get_expected_sessions(animal, new_date)
        if record.milking_session not in expected:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "SESSION_NOT_EXPECTED",
                    "animal_id": record.animal_id,
                    "production_date": new_date.isoformat(),
                    "milking_session": record.milking_session,
                    "expected_sessions": expected,
                },
            )
        existing = factory.milk().ledger_row_for_animal_day(record.animal_id, new_date)
        if existing is not None and existing.id != record.id:
            raise HTTPException(status_code=409, detail="Another governed milk row already exists for this animal/date")

    values = {
        "morning_yield": patch.morning_yield,
        "afternoon_yield": patch.afternoon_yield,
        "evening_yield": patch.evening_yield,
    }
    for field, value in values.items():
        if value is not None:
            setattr(record, field, float(value))

    if not any(
        getattr(record, field, None) is not None
        for field in ("morning_yield", "afternoon_yield", "evening_yield")
    ):
        raise HTTPException(status_code=422, detail="At least one milk yield must remain recorded")

    record.production_date = datetime.combine(new_date, record.production_date.time())
    record.notes = patch.notes if patch.notes is not None else record.notes
    record.recorded_at = utcnow()
    record.calculate_total()
    session.add(record)
    session.flush()
    after = _production_payload(record)
    correction = _record_milk_correction(
        container=container,
        production_id=record.id,
        action="UPDATE",
        reason=reason,
        operator=operator,
        before=before,
        after=after,
        source_request_id=patch.request_id,
    )
    if not session.info.get("operational_write_managed", False):
        session.commit()
    session.refresh(record)
    result = _production_payload(record)
    result["correction_id"] = correction.id
    return result


@router.post("/production/{record_id}/void")
@operational_write
def void_milk_production(
    record_id: int,
    request: VoidRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    session = container.repository_factory.session
    record = (
        session.query(MilkProduction)
        .filter(MilkProduction.id == record_id)
        .with_for_update()
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Milk production record not found")
    if str(record.status).upper() == "VOID":
        return _production_payload(record)

    reason = _meaningful_correction_reason(request.reason)
    operator = _operator(current_user, request.operator)
    snapshot = _production_payload(record)
    record.notes = _append_void_note(record.notes, reason, snapshot)
    # Keep the VOID row permanently visible as audit history while releasing
    # the unique governed-day slot for a future replacement row.
    record.session_ledger = False
    record.morning_yield = None
    record.afternoon_yield = None
    record.evening_yield = None
    record.total_yield = None
    record.status = "VOID"
    record.recorded_at = utcnow()
    session.add(record)
    session.flush()
    after = _production_payload(record)
    correction = _record_milk_correction(
        container=container,
        production_id=record.id,
        action="VOID",
        reason=reason,
        operator=operator,
        before=snapshot,
        after=after,
        source_request_id=request.request_id,
    )
    if not session.info.get("operational_write_managed", False):
        session.commit()
    session.refresh(record)
    result = _production_payload(record)
    result["correction_id"] = correction.id
    return result


@router.get("/production/{record_id}/corrections")
def milk_production_corrections(
    record_id: int,
    container=Depends(get_container),
):
    factory = container.repository_factory
    record = factory.session.get(MilkProduction, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Milk production record not found")

    rows = factory.milk_corrections().get_for_production(record_id)
    return {
        "data_status": "LIVE_PERSISTED",
        "production_id": record_id,
        "corrections": [
            {
                "id": row.id,
                "action": row.action,
                "reason": row.reason,
                "operator": row.operator,
                "before": row.before_json,
                "after": row.after_json,
                "source_request_id": row.source_request_id,
                "corrected_at": _iso(row.corrected_at),
            }
            for row in rows
        ],
    }


@router.post("/dispositions")
@operational_write
def create_milk_disposition(
    entry: DispositionCreate,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    try:
        item = MilkReconciliationService(
            container.repository_factory.milk_dispositions(),
            production_repository=container.repository_factory.milk(),
        ).record_disposition(
            production_date=entry.production_date,
            disposition_type=entry.disposition_type,
            quantity_litres=entry.quantity_litres,
            sale_id=entry.sale_id,
            counterparty=entry.counterparty,
            selling_price_per_litre=entry.selling_price_per_litre,
            notes=entry.notes,
            recorded_by=_operator(current_user),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    container.input_gateway.record(
        "milk_disposition",
        entry.model_dump(mode="json"),
        _operator(current_user),
    )
    return _disposition_payload(item)


@router.patch("/dispositions/{disposition_id}")
@operational_write
def update_milk_disposition(
    disposition_id: int,
    patch: DispositionPatch,
    container=Depends(get_container),
):
    # Milk and Finance are two persisted projections of one linked commercial
    # sale. A linked amendment must either update both or neither.
    factory = container.repository_factory

    try:
        with factory.session.begin_nested():
            session = factory.session

            item = (
                session.query(MilkDisposition)
                .filter(MilkDisposition.id == disposition_id)
                .with_for_update()
                .first()
            )

            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail="Milk disposition not found",
                )

            if str(item.status).upper() == "VOID":
                raise HTTPException(
                    status_code=409,
                    detail="VOID milk disposition cannot be edited",
                )

            linked_finance = _primary_finance_sale_for_disposition(
                session,
                item,
                lock=True,
            )

            new_date = patch.production_date or item.production_date
            new_qty = (
                float(patch.quantity_litres)
                if patch.quantity_litres is not None
                else float(item.quantity_litres)
            )

            production_basis = MilkReconciliationService._production_total(
                new_date,
                production_repository=factory.milk(),
            )

            existing_dispositions = (
                factory.milk_dispositions().get_by_date(new_date)
            )

            try:
                MilkReconciliationService.validate_disposition_quantity(
                    production_basis=production_basis,
                    dispositions=existing_dispositions,
                    disposition_type=item.disposition_type,
                    quantity_litres=new_qty,
                    exclude_id=item.id,
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=422,
                    detail=str(exc),
                ) from exc

            item.production_date = new_date
            item.quantity_litres = new_qty

            if patch.counterparty is not None:
                item.counterparty = patch.counterparty

            if patch.selling_price_per_litre is not None:
                item.selling_price_per_litre = Decimal(
                    str(patch.selling_price_per_litre)
                ).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_HALF_UP,
                )

            if patch.notes is not None:
                item.notes = patch.notes

            if item.disposition_type == "SOLD":
                if (
                    item.selling_price_per_litre is None
                    or Decimal(str(item.selling_price_per_litre)) < 0
                ):
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            "SOLD disposition requires a non-negative "
                            "selling price"
                        ),
                    )

                rate = Decimal(
                    str(item.selling_price_per_litre)
                ).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_HALF_UP,
                )

                amount_due = (
                    Decimal(str(item.quantity_litres)) * rate
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )

                item.selling_price_per_litre = rate
                item.amount_due = amount_due
            else:
                item.amount_due = Decimal("0.00")

            if linked_finance is not None:
                linked_finance.quantity = new_qty
                linked_finance.unit_rate = item.selling_price_per_litre
                linked_finance.amount = item.amount_due
                linked_finance.counterparty = item.counterparty

                existing_dt = linked_finance.transaction_date
                existing_time = (
                    existing_dt.time()
                    if existing_dt is not None
                    else datetime.min.time()
                )
                linked_finance.transaction_date = datetime.combine(
                    new_date,
                    existing_time,
                )

                finance_status = str(
                    linked_finance.status or "RECORDED"
                ).upper()

                if finance_status in {"PAID", "RECEIVED"}:
                    item.amount_received = item.amount_due
                elif finance_status == "RECEIVABLE":
                    item.amount_received = Decimal("0.00")

                session.add(linked_finance)

            item.updated_at = utcnow()
            session.add(item)
            session.flush()

            result = _disposition_payload(item)

        container.input_gateway.record(
            "milk_disposition_amendment",
            {"disposition_id": disposition_id, **patch.model_dump(mode="json")},
            "API",
        )
        return result
    except Exception:
        raise


@router.post("/dispositions/{disposition_id}/void")
@operational_write
def void_milk_disposition(
    disposition_id: int,
    request: VoidRequest,
    container=Depends(get_container),
):
    factory = container.repository_factory

    try:
        with factory.session.begin_nested():
            session = factory.session

            item = (
                session.query(MilkDisposition)
                .filter(MilkDisposition.id == disposition_id)
                .with_for_update()
                .first()
            )

            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail="Milk disposition not found",
                )

            if str(item.status).upper() == "VOID":
                return _disposition_payload(item)

            if Decimal(str(item.amount_received or 0)) > 0:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A disposition with received cash cannot be voided "
                        "in Milk phase CRUD."
                    ),
                )

            linked_finance = _primary_finance_sale_for_disposition(
                session,
                item,
                lock=True,
            )

            snapshot = _disposition_payload(item)

            item.notes = _append_void_note(
                item.notes,
                request.reason,
                snapshot,
            )
            item.quantity_litres = 0.0
            item.amount_due = Decimal("0.00")
            item.status = "VOID"
            item.updated_at = utcnow()

            if linked_finance is not None:
                current_finance_status = str(
                    linked_finance.status or "RECORDED"
                ).upper()

                if current_finance_status in {"PAID", "RECEIVED"}:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "A settled Finance-linked milk sale must be "
                            "reversed through the governed Finance workflow."
                        ),
                    )

                linked_finance.status = "VOID"
                linked_finance.notes = (
                    f"{linked_finance.notes or ''}\n"
                    f"VOIDED_FROM_MILK REASON={request.reason}"
                ).strip()

                session.add(linked_finance)

            session.add(item)
            session.flush()

            result = _disposition_payload(item)

        container.input_gateway.record(
            "milk_disposition_void",
            {"disposition_id": disposition_id, **request.model_dump(mode="json")},
            "API",
        )
        return result
    except Exception:
        raise
