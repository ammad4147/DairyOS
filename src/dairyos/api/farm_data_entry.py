from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from dairyos.api.auth import get_optional_current_user
from dairyos.api.dependencies import get_container

from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.health_observation import HealthObservation
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.treatment_record import TreatmentRecord
from dairyos.farm.operations.models.breeding_record import BreedingRecord
from dairyos.milk.models.milking_session import MilkingSession
from dairyos.milk.services.milk_recording_intelligence_service import (
    MilkRecordingIntelligenceService,
)

from dairyos.operations.intelligence.services.withdrawal_service import (
    WithdrawalPeriod,
)

from dairyos.data.repositories.repository_factory import (
    RepositoryFactory,
)


router = APIRouter(
    prefix="/farm",
    tags=["Farm Data Entry"],
)


class BaseEntryRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    operator: str = Field(
        default="API",
        min_length=1,
    )


class MilkEntryRequest(BaseEntryRequest):
    animal_id: str
    morning_yield: float = 0.0
    afternoon_yield: float = 0.0
    evening_yield: float = 0.0
    milking_session: MilkingSession


class LegacyCompatibleMilkEntryRequest(BaseEntryRequest):
    """
    HTTP compatibility boundary for historical /farm/milk callers.

    The governed MilkEntryRequest deliberately requires milking_session.
    Older clients, however, historically omitted it. Such requests are
    normalized to MORNING before entering the governed request model.
    """

    animal_id: str
    morning_yield: float = 0.0
    afternoon_yield: float = 0.0
    evening_yield: float = 0.0
    milking_session: MilkingSession | None = None

    def to_governed_request(self) -> MilkEntryRequest:
        payload = self.model_dump()
        if payload.get("milking_session") is None:
            payload["milking_session"] = MilkingSession.MORNING

        return MilkEntryRequest.model_validate(payload)


class FeedEntryRequest(BaseEntryRequest):
    feed_type: str
    quantity_kg: float
    group_or_pen: str | None = None
    animal_id: str | None = None


class HealthEntryRequest(BaseEntryRequest):
    animal_id: str
    observation: str | None = None
    symptom: str | None = None
    temperature_c: float | None = None
    severity: str = "NORMAL"


class TreatmentEntryRequest(BaseEntryRequest):
    animal_id: str
    medicine: str
    diagnosis: str | None = None
    dose: str | None = None
    treated_by: str | None = None
    milk_withdrawal_days: float | None = None
    notes: str | None = None


class DrugReferenceEntryRequest(BaseEntryRequest):
    medicine: str
    milk_withdrawal_days: float
    meat_withdrawal_days: float | None = None
    notes: str | None = None
    verified: bool = False


class BreedingEntryRequest(BaseEntryRequest):
    animal_id: str
    event_type: str
    technician: str | None = None
    result: str | None = None
    semen_or_bull: str | None = None
    notes: str | None = None


class WorkforceEntryRequest(BaseEntryRequest):
    worker_id: str
    activity: str
    task: str | None = None
    status: str | None = None
    hours: float | None = None
    location: str | None = None
    notes: str | None = None


class InventoryEntryRequest(BaseEntryRequest):
    item: str
    quantity: float
    movement_type: str | None = None
    unit: str | None = None
    location: str | None = None
    supplier: str | None = None
    notes: str | None = None


class EquipmentEntryRequest(BaseEntryRequest):
    equipment_id: str
    activity: str
    status: str | None = None
    running_hours: float | None = None
    location: str | None = None
    notes: str | None = None


class FinancialEntryRequest(BaseEntryRequest):
    transaction_type: str
    amount: float
    category: str | None = None
    payment_method: str | None = None
    counterparty: str | None = None
    notes: str | None = None


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _operator(
    payload: dict[str, Any],
    current_user: dict[str, Any] | None,
) -> str:
    if current_user is not None:
        return str(current_user["sub"])

    return str(payload.get("operator") or "API")


def _record(
    container,
    input_type: str,
    payload: dict[str, Any],
    current_user: dict[str, Any] | None = None,
):
    """Persist domain data before publishing the operational input event.

    Repository-backed inputs therefore cannot advertise an accepted
    operational event when their domain record failed to persist. Inputs
    without a domain repository (workforce/inventory/equipment) remain
    authoritative through the durable operational-input repository/event
    stream.
    """
    operator = _operator(payload, current_user)

    canonical_payload = {
        **payload,
        "operator": operator,
        "timestamp": payload.get("timestamp") or _timestamp(),
    }

    rf = getattr(container, "repository_factory", None)
    owns_factory = False
    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True

    try:
        if input_type == "milk_production":
            milk_repo = rf.milk()
            production = MilkProduction(
                animal_id=str(payload.get("animal_id")),
                milking_session=str(payload.get("milking_session")),
                morning_yield=float(payload.get("morning_yield", 0.0)),
                afternoon_yield=float(payload.get("afternoon_yield", 0.0)),
                evening_yield=float(payload.get("evening_yield", 0.0)),
                total_yield=float(
                    payload.get(
                        "total_yield",
                        payload.get("litres", 0.0),
                    )
                ),
                status=payload.get("status", "RECORDED"),
            )
            if hasattr(milk_repo, "save"):
                milk_repo.save(production)
            else:
                milk_repo.add(production)

        elif input_type == "feeding":
            feed_repo = rf.feed()
            record = FeedRecord(
                animal_id=payload.get("animal_id"),
                group_or_pen=payload.get("group_or_pen"),
                feed_type=payload.get("feed_type", "DEFAULT"),
                quantity_kg=float(payload.get("quantity_kg", 0.0)),
                notes=payload.get("notes"),
                status=payload.get("status", "RECORDED"),
            )
            if hasattr(feed_repo, "save"):
                feed_repo.save(record)
            else:
                feed_repo.add(record)

        elif input_type == "animal_health":
            health_repo = rf.health()
            observation = HealthObservation(
                animal_id=str(payload.get("animal_id")),
                observation=payload.get("observation"),
                symptom=payload.get("symptom"),
                temperature=(
                    payload.get("temperature_c")
                    or payload.get("temperature")
                ),
                temperature_c=payload.get("temperature_c"),
                reported_by=operator,
                severity=payload.get("severity", "NORMAL"),
                status=payload.get("status", "OPEN"),
            )
            if hasattr(health_repo, "save"):
                health_repo.save(observation)
            else:
                health_repo.add(observation)

        elif input_type == "breeding":
            breeding_repo = rf.breeding()
            record = BreedingRecord(
                animal_id=str(payload.get("animal_id")),
                event_type=str(payload.get("event_type")),
                result=str(payload.get("result") or "RECORDED"),
                technician=str(
                    payload.get("technician") or operator
                ),
            )
            breeding_repo.save(record)

        elif input_type == "financial":
            finance_repo = rf.financial()
            transaction = FinancialTransaction(
                transaction_type=payload.get(
                    "transaction_type",
                    "EXPENSE",
                ),
                category=(payload.get("category") or "GENERAL"),
                amount=float(payload.get("amount", 0.0)),
                reference=(
                    payload.get("counterparty")
                    or payload.get("notes")
                    or ""
                ),
                status=payload.get("status", "RECORDED"),
                animal_id=payload.get("animal_id"),
                currency=payload.get("currency", "PKR"),
            )
            if hasattr(finance_repo, "save"):
                finance_repo.save(transaction)
            else:
                finance_repo.add(transaction)

        event = container.input_gateway.record(
            input_type=input_type,
            payload=canonical_payload,
            actor=operator,
        )
        event_payload = dict(
            getattr(event, "payload", {}) or {}
        )

    except Exception as exc:
        try:
            rf.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=(
                "Operational input persistence failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
    finally:
        if owns_factory:
            rf.close()

    return {
        **canonical_payload,
        **event_payload,
        "status": canonical_payload.get(
            "status",
            "RECORDED",
        ),
    }


def _list_by_type(container, input_type: str):
    records = []
    for event in container.event_journal.all_events():
        if (
            event.name == "OperationalInputReceived"
            and event.payload.get("input_type") == input_type
        ):
            records.append(event.payload)
    return records


@router.post("/milk")
def record_milk_entry(
    entry: LegacyCompatibleMilkEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    governed_entry = entry.to_governed_request()

    total = (
        governed_entry.morning_yield
        + governed_entry.afternoon_yield
        + governed_entry.evening_yield
    )
    status = "RECORDED"
    withdrawal_warning = False
    safety_message = None

    withdrawal_svc = getattr(
        container,
        "withdrawal_service",
        None,
    )

    if withdrawal_svc and withdrawal_svc.is_animal_withdrawn(
        governed_entry.animal_id
    ):
        status = "WITHHELD"
        withdrawal_warning = True
        safety_message = (
            f"SAFETY ALERT: Animal {governed_entry.animal_id} is under "
            "active treatment withdrawal. Milk must be withheld!"
        )

    payload = {
        **governed_entry.model_dump(),
        "milking_session": governed_entry.milking_session.value,
        "litres": total,
        "total_yield": total,
        "status": status,
        "withdrawal_warning": withdrawal_warning,
    }

    if safety_message:
        payload["safety_message"] = safety_message

    return _record(
        container,
        "milk_production",
        payload,
        current_user,
    )


@router.get("/milk")
def list_milk_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "milk_production",
    )


@router.post("/feed")
def record_feed_entry(
    entry: FeedEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "feeding",
        {
            **entry.model_dump(),
            "status": "RECORDED",
        },
        current_user,
    )


@router.get("/milk/intelligence")
def milk_recording_intelligence(
    threshold_percent: float = 20.0,
    container=Depends(get_container),
):
    rf = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True

    try:
        service = MilkRecordingIntelligenceService(
            rf.milk()
        )
        return service.dashboard(
            threshold_percent=max(
                1.0,
                min(100.0, threshold_percent),
            )
        )
    finally:
        if owns_factory:
            rf.close()


@router.get("/feed")
def list_feed_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "feeding",
    )


@router.post("/health-observations")
def record_health_observation(
    entry: HealthEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    payload = entry.model_dump()
    payload["observation"] = (
        entry.observation
        or entry.symptom
        or "Observation recorded"
    )
    payload["status"] = "OPEN"

    return _record(
        container,
        "animal_health",
        payload,
        current_user,
    )


@router.get("/health-observations")
def list_health_observations(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "animal_health",
    )


@router.post("/treatments")
def record_treatment(
    entry: TreatmentEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    operator = _operator(
        entry.model_dump(),
        current_user,
    )

    rf = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if rf is None:
        rf = RepositoryFactory.create()
        owns_factory = True

    try:
        reference = None
        reference_repo = getattr(
            container,
            "drug_reference_repository",
            None,
        )

        if reference_repo is not None:
            reference = reference_repo.find_by_medicine(
                entry.medicine
            )

        withdrawal_source = "reference_table"
        withdrawal_days = None

        if reference is not None:
            withdrawal_days = float(
                reference.milk_withdrawal_days
            )

            if entry.milk_withdrawal_days is not None:
                withdrawal_days = max(
                    withdrawal_days,
                    float(entry.milk_withdrawal_days),
                )

                if (
                    withdrawal_days
                    > float(reference.milk_withdrawal_days)
                ):
                    withdrawal_source = "override_extended"

        elif entry.milk_withdrawal_days is not None:
            withdrawal_days = float(
                entry.milk_withdrawal_days
            )
            withdrawal_source = "manual_override"

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unknown medicine '{entry.medicine}': "
                    "not found in the drug reference table "
                    "and no milk_withdrawal_days was supplied "
                    "on this treatment."
                ),
            )

        if withdrawal_days < 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "milk_withdrawal_days cannot be negative."
                ),
            )

        treated_at = datetime.now(timezone.utc)
        withdrawal_until = (
            treated_at
            + timedelta(days=withdrawal_days)
        )

        treatment_repo = (
            getattr(
                container,
                "treatment_repository",
                None,
            )
            or rf.treatment()
        )

        record = TreatmentRecord(
            animal_id=entry.animal_id,
            diagnosis=entry.diagnosis,
            medicine=entry.medicine,
            dose=entry.dose,
            treated_by=entry.treated_by or operator,
            treated_at=treated_at,
            milk_withdrawal_days=withdrawal_days,
            milk_withdrawal_until=withdrawal_until,
            withdrawal_source=withdrawal_source,
            notes=entry.notes,
        )

        treatment_repo.add(record)

        withdrawal_svc = getattr(
            container,
            "withdrawal_service",
            None,
        )

        if withdrawal_svc is not None:
            withdrawal_svc.add_period(
                WithdrawalPeriod(
                    treatment_id=str(record.id),
                    animal_id=entry.animal_id,
                    start_time=treated_at,
                    end_time=withdrawal_until,
                )
            )

        canonical_payload = {
            **entry.model_dump(),
            "operator": operator,
            "treatment_id": record.id,
            "treated_at": treated_at.isoformat(),
            "milk_withdrawal_days": withdrawal_days,
            "milk_withdrawal_until": (
                withdrawal_until.isoformat()
            ),
            "withdrawal_source": withdrawal_source,
            "status": "RECORDED",
        }

        event = container.input_gateway.record(
            input_type="treatment",
            payload=canonical_payload,
            actor=operator,
        )

        event_payload = dict(
            getattr(event, "payload", {}) or {}
        )

        return {
            **canonical_payload,
            **event_payload,
        }

    finally:
        if owns_factory:
            rf.close()


@router.get("/treatments")
def list_treatments(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "treatment",
    )


@router.get("/withdrawals/active")
def list_active_withdrawals(
    container=Depends(get_container),
):
    treatment_repo = getattr(
        container,
        "treatment_repository",
        None,
    )
    withdrawal_svc = getattr(
        container,
        "withdrawal_service",
        None,
    )

    if (
        treatment_repo is None
        or withdrawal_svc is None
    ):
        return []

    now = datetime.now(timezone.utc)
    active = []

    for record in treatment_repo.get_all():
        if withdrawal_svc.is_withdrawn(
            str(record.id),
            at=now,
        ):
            active.append(
                {
                    "treatment_id": record.id,
                    "animal_id": record.animal_id,
                    "medicine": record.medicine,
                    "treated_at": (
                        record.treated_at.isoformat()
                        if record.treated_at
                        else None
                    ),
                    "milk_withdrawal_until": (
                        record.milk_withdrawal_until.isoformat()
                        if record.milk_withdrawal_until
                        else None
                    ),
                }
            )

    return active


@router.get("/drug-reference")
def list_drug_reference(
    container=Depends(get_container),
):
    reference_repo = getattr(
        container,
        "drug_reference_repository",
        None,
    )

    if reference_repo is None:
        return []

    return [
        {
            "id": row.id,
            "medicine": row.medicine,
            "milk_withdrawal_days": (
                row.milk_withdrawal_days
            ),
            "meat_withdrawal_days": (
                row.meat_withdrawal_days
            ),
            "notes": row.notes,
            "verified": row.verified,
            "updated_by": row.updated_by,
            "updated_at": (
                row.updated_at.isoformat()
                if row.updated_at
                else None
            ),
        }
        for row in reference_repo.get_all()
    ]


@router.post("/drug-reference")
def upsert_drug_reference(
    entry: DrugReferenceEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    operator = _operator(
        entry.model_dump(),
        current_user,
    )

    reference_repo = getattr(
        container,
        "drug_reference_repository",
        None,
    )

    if reference_repo is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Drug reference repository is not available."
            ),
        )

    record = reference_repo.upsert(
        medicine=entry.medicine,
        milk_withdrawal_days=(
            entry.milk_withdrawal_days
        ),
        meat_withdrawal_days=(
            entry.meat_withdrawal_days
        ),
        notes=entry.notes,
        verified=entry.verified,
        updated_by=operator,
    )

    return {
        "id": record.id,
        "medicine": record.medicine,
        "milk_withdrawal_days": (
            record.milk_withdrawal_days
        ),
        "meat_withdrawal_days": (
            record.meat_withdrawal_days
        ),
        "notes": record.notes,
        "verified": record.verified,
        "updated_by": record.updated_by,
    }


@router.post("/breeding")
def record_breeding_entry(
    entry: BreedingEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "breeding",
        entry.model_dump(),
        current_user,
    )


@router.get("/breeding")
def list_breeding_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "breeding",
    )


@router.post("/workforce")
def record_workforce_entry(
    entry: WorkforceEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "workforce",
        entry.model_dump(),
        current_user,
    )


@router.get("/workforce")
def list_workforce_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "workforce",
    )


@router.post("/inventory")
def record_inventory_entry(
    entry: InventoryEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "inventory",
        entry.model_dump(),
        current_user,
    )


@router.get("/inventory")
def list_inventory_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "inventory",
    )


@router.post("/equipment")
def record_equipment_entry(
    entry: EquipmentEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "equipment",
        entry.model_dump(),
        current_user,
    )


@router.get("/equipment")
def list_equipment_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "equipment",
    )


@router.post("/financial")
def record_financial_entry(
    entry: FinancialEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    return _record(
        container,
        "financial",
        entry.model_dump(),
        current_user,
    )


@router.get("/financial")
def list_financial_entries(
    container=Depends(get_container),
):
    return _list_by_type(
        container,
        "financial",
    )
