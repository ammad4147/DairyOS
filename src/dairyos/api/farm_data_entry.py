from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from dairyos.api.auth import get_current_user, get_optional_current_user
from dairyos.api.dependencies import get_container

router = APIRouter(prefix="/farm", tags=["Farm Data Entry"])


class BaseEntryRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    operator: str = Field(default="API", min_length=1)


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
    worker_id: str | None = None
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


def _record(
    container,
    input_type: str,
    payload: dict[str, Any],
    authenticated_user: dict[str, Any] | None = None,
):
    supplied_operator = str(payload.get("operator") or "API")
    operator = (
        str(authenticated_user["sub"])
        if authenticated_user is not None
        else supplied_operator
    )
    canonical_payload = {
        **payload,
        "operator": operator,
        "timestamp": payload.get("timestamp") or _timestamp(),
    }
    event = container.input_gateway.record(
        input_type=input_type,
        payload=canonical_payload,
        actor=operator,
    )
    event_payload = dict(getattr(event, "payload", {}) or {})
    return {
        **canonical_payload,
        **event_payload,
        "status": canonical_payload.get("status", "RECORDED"),
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
    entry: MilkEntryRequest,
    container=Depends(get_container),
    authenticated_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    total = entry.morning_yield + entry.afternoon_yield + entry.evening_yield
    return _record(
        container,
        "milk_production",
        {**entry.model_dump(), "litres": total, "total_yield": total, "status": "RECORDED"},
        authenticated_user,
    )


@router.get("/milk")
def list_milk_entries(container=Depends(get_container)):
    return _list_by_type(container, "milk_production")


@router.post("/feed")
def record_feed_entry(
    entry: FeedEntryRequest,
    container=Depends(get_container),
    authenticated_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    return _record(container, "feeding", {**entry.model_dump(), "status": "RECORDED"}, authenticated_user)


@router.get("/feed")
def list_feed_entries(container=Depends(get_container)):
    return _list_by_type(container, "feeding")


@router.post("/health-observations")
def record_health_observation(
    entry: HealthEntryRequest,
    container=Depends(get_container),
    authenticated_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    payload = entry.model_dump()
    payload["observation"] = entry.observation or entry.symptom or "Observation recorded"
    payload["status"] = "OPEN"
    return _record(container, "animal_health", payload, authenticated_user)


@router.get("/health-observations")
def list_health_observations(container=Depends(get_container)):
    return _list_by_type(container, "animal_health")


@router.post("/breeding")
def record_breeding_entry(
    entry: BreedingEntryRequest,
    container=Depends(get_container),
    authenticated_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    return _record(container, "breeding", entry.model_dump(), authenticated_user)


@router.get("/breeding")
def list_breeding_entries(container=Depends(get_container)):
    return _list_by_type(container, "breeding")


@router.post("/workforce")
def record_workforce_entry(
    entry: WorkforceEntryRequest,
    container=Depends(get_container),
    authenticated_user: dict[str, Any] = Depends(get_current_user),
):
    payload = entry.model_dump()
    payload["worker_id"] = authenticated_user["sub"]
    payload["worker_name"] = authenticated_user["name"]
    payload["worker_role"] = authenticated_user["role"]
    payload["farm_id"] = authenticated_user["farm_id"]
    return _record(container, "workforce", payload, authenticated_user)


@router.get("/workforce")
def list_workforce_entries(container=Depends(get_container)):
    return _list_by_type(container, "workforce")


@router.post("/inventory")
def record_inventory_entry(
    entry: InventoryEntryRequest,
    container=Depends(get_container),
    authenticated_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    return _record(container, "inventory", entry.model_dump(), authenticated_user)


@router.get("/inventory")
def list_inventory_entries(container=Depends(get_container)):
    return _list_by_type(container, "inventory")


@router.post("/equipment")
def record_equipment_entry(
    entry: EquipmentEntryRequest,
    container=Depends(get_container),
    authenticated_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    return _record(container, "equipment", entry.model_dump(), authenticated_user)


@router.get("/equipment")
def list_equipment_entries(container=Depends(get_container)):
    return _list_by_type(container, "equipment")


@router.post("/financial")
def record_financial_entry(
    entry: FinancialEntryRequest,
    container=Depends(get_container),
    authenticated_user: dict[str, Any] | None = Depends(get_optional_current_user),
):
    return _record(container, "financial", entry.model_dump(), authenticated_user)


@router.get("/financial")
def list_financial_entries(container=Depends(get_container)):
    return _list_by_type(container, "financial")
