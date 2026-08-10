from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from dairyos.api.auth import get_optional_current_user
from dairyos.api.dependencies import get_container

from dairyos.data.models.milk_production import MilkProduction
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.health_observation import HealthObservation
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.milk.services.milk_recording_intelligence_service import MilkRecordingIntelligenceService

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
    milking_session: str | None = None


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
    """
    Resolve the authoritative operator identity.

    Authenticated identity wins over a client-supplied operator field.
    """

    if current_user is not None:
        return str(current_user["sub"])

    return str(
        payload.get("operator")
        or "API"
    )


def _record(
    container,
    input_type: str,
    payload: dict[str, Any],
    current_user: dict[str, Any] | None = None,
):
    """
    Record an operational input through the canonical gateway and,
    where a relational repository exists, persist the corresponding
    operational record.

    Database failures are deliberately NOT swallowed.

    A successful HTTP response must mean that the requested
    persistence operation succeeded.
    """

    operator = _operator(
        payload,
        current_user,
    )

    canonical_payload = {
        **payload,
        "operator": operator,
        "timestamp": (
            payload.get("timestamp")
            or _timestamp()
        ),
    }

    event = container.input_gateway.record(
        input_type=input_type,
        payload=canonical_payload,
        actor=operator,
    )

    event_payload = dict(
        getattr(event, "payload", {})
        or {}
    )

    rf = getattr(
        container,
        "repository_factory",
        None,
    )

    if rf is None:
        rf = RepositoryFactory.create()

    try:
        if input_type == "milk_production":

            milk_repo = rf.milk()

            production = MilkProduction(
                animal_id=str(
                    payload.get("animal_id")
                ),
                morning_yield=float(
                    payload.get(
                        "morning_yield",
                        0.0,
                    )
                ),
                afternoon_yield=float(
                    payload.get(
                        "afternoon_yield",
                        0.0,
                    )
                ),
                evening_yield=float(
                    payload.get(
                        "evening_yield",
                        0.0,
                    )
                ),
                total_yield=float(
                    payload.get(
                        "total_yield",
                        payload.get(
                            "litres",
                            0.0,
                        ),
                    )
                ),
                status=payload.get(
                    "status",
                    "RECORDED",
                ),
            )

            if hasattr(milk_repo, "save"):
                milk_repo.save(production)
            else:
                milk_repo.add(production)

        elif input_type == "feeding":

            feed_repo = rf.feed()

            record = FeedRecord(
                animal_id=payload.get(
                    "animal_id"
                ),
                group_or_pen=payload.get(
                    "group_or_pen"
                ),
                feed_type=payload.get(
                    "feed_type",
                    "DEFAULT",
                ),
                quantity_kg=float(
                    payload.get(
                        "quantity_kg",
                        0.0,
                    )
                ),
                notes=payload.get(
                    "notes"
                ),
                status=payload.get(
                    "status",
                    "RECORDED",
                ),
            )

            if hasattr(feed_repo, "save"):
                feed_repo.save(record)
            else:
                feed_repo.add(record)

        elif input_type == "animal_health":

            health_repo = rf.health()

            observation = HealthObservation(
                animal_id=str(
                    payload.get("animal_id")
                ),
                observation=payload.get(
                    "observation"
                ),
                symptom=payload.get(
                    "symptom"
                ),
                temperature=(
                    payload.get(
                        "temperature_c"
                    )
                    or payload.get(
                        "temperature"
                    )
                ),
                temperature_c=payload.get(
                    "temperature_c"
                ),
                reported_by=operator,
                severity=payload.get(
                    "severity",
                    "NORMAL",
                ),
                status=payload.get(
                    "status",
                    "OPEN",
                ),
            )

            if hasattr(health_repo, "save"):
                health_repo.save(observation)
            else:
                health_repo.add(observation)

        elif input_type == "financial":

            finance_repo = rf.financial()

            transaction = FinancialTransaction(
                transaction_type=payload.get(
                    "transaction_type",
                    "EXPENSE",
                ),
                category=(payload.get("category") or "GENERAL"),
                amount=float(
                    payload.get(
                        "amount",
                        0.0,
                    )
                ),
                reference=(
                    payload.get(
                        "counterparty"
                    )
                    or payload.get(
                        "notes"
                    )
                    or ""
                ),
                status=payload.get(
                    "status",
                    "RECORDED",
                ),
                animal_id=payload.get(
                    "animal_id"
                ),
                currency=payload.get(
                    "currency",
                    "PKR",
                ),
            )

            if hasattr(finance_repo, "save"):
                finance_repo.save(transaction)
            else:
                finance_repo.add(transaction)

    except Exception as exc:
        try:
            rf.rollback()
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=(
                f"Operational input persistence failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

    return {
        **canonical_payload,
        **event_payload,
        "status": canonical_payload.get(
            "status",
            "RECORDED",
        ),
    }


def _list_by_type(
    container,
    input_type: str,
):
    records = []

    for event in container.event_journal.all_events():
        if (
            event.name
            == "OperationalInputReceived"
            and event.payload.get(
                "input_type"
            )
            == input_type
        ):
            records.append(
                event.payload
            )

    return records


@router.post("/milk")
def record_milk_entry(
    entry: MilkEntryRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    total = (
        entry.morning_yield
        + entry.afternoon_yield
        + entry.evening_yield
    )

    status = "RECORDED"
    withdrawal_warning = False
    safety_message = None

    withdrawal_svc = getattr(
        container,
        "withdrawal_service",
        None,
    )

    if (
        withdrawal_svc
        and withdrawal_svc.is_animal_withdrawn(
            entry.animal_id
        )
    ):
        status = "WITHHELD"
        withdrawal_warning = True
        safety_message = (
            "SAFETY ALERT: Animal "
            f"{entry.animal_id} is under active "
            "treatment withdrawal. Milk must be "
            "withheld!"
        )

    payload = {
        **entry.model_dump(),
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

    if rf is None:
        rf = RepositoryFactory.create()

    service = MilkRecordingIntelligenceService(
        rf.milk()
    )

    return service.dashboard(
        threshold_percent=max(
            1.0,
            min(
                100.0,
                threshold_percent,
            ),
        )
    )

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


