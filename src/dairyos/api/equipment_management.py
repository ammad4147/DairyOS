from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from dairyos.api.auth import get_optional_current_user
from dairyos.api.dependencies import get_container
from dairyos.core.time_utils import utcnow
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)


router = APIRouter(
    prefix="/farm/equipment",
    tags=["Equipment Management"],
)


EQUIPMENT_STATUS_ALIASES = {
    "AVAILABLE": "AVAILABLE",
    "IN_USE": "IN_USE",
    "MAINTENANCE": "MAINTENANCE",
    "OUT_OF_SERVICE": "OUT_OF_SERVICE",
    # Legacy compatibility accepted at the HTTP boundary.
    "OPERATIONAL": "AVAILABLE",
}

EQUIPMENT_CONDITIONS = {
    "GOOD",
    "FAIR",
    "POOR",
}


class EquipmentRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    equipment_id: str = Field(min_length=1, max_length=100)
    name: str | None = None
    category: str | None = None
    farm_id: str = "DEFAULT"
    activity: str | None = None
    status: str | None = None
    condition: str | None = None
    running_hours: float | None = Field(default=None, ge=0)
    location: str | None = None
    commissioned_at: datetime | None = None
    last_service_at: datetime | None = None
    next_service_due_at: datetime | None = None
    active: bool | None = None
    event_date: date | None = None
    notes: str | None = None
    operator: str | None = None


class EquipmentPatchRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    category: str | None = None
    location: str | None = None
    status: str | None = None
    condition: str | None = None
    running_hours: float | None = Field(default=None, ge=0)
    commissioned_at: datetime | None = None
    last_service_at: datetime | None = None
    next_service_due_at: datetime | None = None
    active: bool | None = None
    notes: str | None = None
    operator: str | None = None


class EquipmentServiceRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_date: date | None = None
    event_type: str = Field(min_length=1)
    running_hours: float | None = Field(default=None, ge=0)
    status_after: str | None = None
    next_service_due_at: datetime | None = None
    notes: str | None = None
    operator: str | None = None


def _operator(
    payload: dict[str, Any],
    current_user: dict[str, Any] | None,
) -> str:
    if current_user is not None:
        return str(current_user["sub"])
    return str(payload.get("operator") or "API")


def _canonical_status(value: str | None) -> str:
    candidate = str(value or "AVAILABLE").upper().strip()
    try:
        return EQUIPMENT_STATUS_ALIASES[candidate]
    except KeyError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                "status must be one of "
                "AVAILABLE, IN_USE, MAINTENANCE, "
                "OUT_OF_SERVICE."
            ),
        ) from exc


def _canonical_condition(value: str | None) -> str:
    candidate = str(value or "GOOD").upper().strip()
    if candidate not in EQUIPMENT_CONDITIONS:
        raise HTTPException(
            status_code=422,
            detail="condition must be GOOD, FAIR, or POOR.",
        )
    return candidate


def _serialize_equipment(entity) -> dict[str, Any]:
    return {
        "id": entity.id,
        "equipment_id": entity.equipment_id,
        "name": entity.name,
        "category": entity.category,
        "farm_id": entity.farm_id,
        "location": entity.location,
        "status": entity.status,
        "condition": entity.condition,
        "running_hours": entity.running_hours,
        "commissioned_at": (
            entity.commissioned_at.isoformat()
            if entity.commissioned_at
            else None
        ),
        "last_service_at": (
            entity.last_service_at.isoformat()
            if entity.last_service_at
            else None
        ),
        "next_service_due_at": (
            entity.next_service_due_at.isoformat()
            if entity.next_service_due_at
            else None
        ),
        "active": entity.active,
        "created_at": entity.created_at.isoformat(),
        "updated_at": entity.updated_at.isoformat(),
    }


def _serialize_service_event(event) -> dict[str, Any]:
    return {
        "id": event.id,
        "equipment_id": event.equipment_id,
        "event_date": event.event_date.isoformat(),
        "event_type": event.event_type,
        "running_hours": event.running_hours,
        "status_before": event.status_before,
        "status_after": event.status_after,
        "operator": event.operator,
        "notes": event.notes,
        "created_at": event.created_at.isoformat(),
    }


def _raise_equipment_findings(
    equipment,
    *,
    operator: str,
) -> None:
    factory = RepositoryFactory.create()
    try:
        findings = OperationalFindingService(
            factory.operational_findings()
        )

        if equipment.status == "OUT_OF_SERVICE":
            findings.raise_or_update(
                source_module="EQUIPMENT",
                severity="HIGH",
                title=(
                    f"Review equipment "
                    f"{equipment.equipment_id}"
                ),
                detail=(
                    f"Equipment {equipment.equipment_id} "
                    "is OUT_OF_SERVICE."
                ),
                subject_type="EQUIPMENT",
                subject_id=equipment.equipment_id,
                route=(
                    f"/farm/equipment/"
                    f"{equipment.equipment_id}"
                ),
                dedupe_key=(
                    f"EQUIPMENT_OUT_OF_SERVICE:"
                    f"{equipment.equipment_id}"
                ),
            )

        if (
            equipment.next_service_due_at is not None
            and equipment.next_service_due_at.date()
            < utcnow().date()
            and equipment.active
        ):
            findings.raise_or_update(
                source_module="EQUIPMENT",
                severity="HIGH",
                title=(
                    f"Equipment service overdue: "
                    f"{equipment.equipment_id}"
                ),
                detail=(
                    f"Scheduled service date "
                    f"{equipment.next_service_due_at.date().isoformat()} "
                    "has passed."
                ),
                subject_type="EQUIPMENT",
                subject_id=equipment.equipment_id,
                route=(
                    f"/farm/equipment/"
                    f"{equipment.equipment_id}"
                ),
                dedupe_key=(
                    f"EQUIPMENT_SERVICE_OVERDUE:"
                    f"{equipment.equipment_id}"
                ),
            )
    finally:
        factory.close()


def _publish_projection_event(
    container,
    *,
    equipment,
    activity: str | None,
    operator: str,
    notes: str | None,
) -> None:
    payload = {
        "input_type": "equipment",
        "equipment_id": equipment.equipment_id,
        "activity": activity or "master_update",
        "status": equipment.status,
        "operator": operator,
        "timestamp": utcnow().isoformat(),
        "details": {
            "equipment_id": equipment.equipment_id,
            "equipment_name": equipment.name,
            "category": equipment.category,
            "operational_status": equipment.status,
            "condition": equipment.condition,
            "running_hours": equipment.running_hours,
            "location": equipment.location,
            "commissioned_at": (
                equipment.commissioned_at.isoformat()
                if equipment.commissioned_at
                else None
            ),
            "last_service_at": (
                equipment.last_service_at.isoformat()
                if equipment.last_service_at
                else None
            ),
            "next_service_due_at": (
                equipment.next_service_due_at.isoformat()
                if equipment.next_service_due_at
                else None
            ),
            "active": equipment.active,
            "notes": notes,
        },
    }

    container.input_gateway.record(
        input_type="equipment",
        payload=payload,
        actor=operator,
    )


@router.post("")
def create_or_update_equipment(
    entry: EquipmentRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    payload = entry.model_dump()
    operator = _operator(payload, current_user)

    status = _canonical_status(entry.status)
    condition = _canonical_condition(entry.condition)

    name = (
        entry.name
        or entry.equipment_id
    )
    category = (
        entry.category
        or "GENERAL"
    )

    factory = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if factory is None:
        factory = RepositoryFactory.create()
        owns_factory = True

    try:
        repository = factory.equipment()

        entity = repository.get_or_create(
            equipment_id=entry.equipment_id,
            name=name,
            category=category,
            farm_id=entry.farm_id,
        )

        before_status = entity.status

        entity = repository.update(
            entity,
            name=name,
            category=category,
            location=entry.location,
            status=status,
            condition=condition,
            running_hours=entry.running_hours,
            commissioned_at=entry.commissioned_at,
            last_service_at=entry.last_service_at,
            next_service_due_at=entry.next_service_due_at,
            active=entry.active,
        )

        event = None
        if entry.activity:
            event = repository.add_service_event(
                equipment_id=entity.equipment_id,
                event_date=(
                    entry.event_date
                    or utcnow().date()
                ),
                event_type=entry.activity,
                running_hours=entry.running_hours,
                status_before=before_status,
                status_after=entity.status,
                operator=operator,
                notes=entry.notes,
            )

        _publish_projection_event(
            container,
            equipment=entity,
            activity=entry.activity,
            operator=operator,
            notes=entry.notes,
        )

    except HTTPException:
        raise
    except Exception as exc:
        try:
            factory.rollback()
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=(
                "Equipment persistence failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
    finally:
        if owns_factory:
            factory.close()

    _raise_equipment_findings(
        entity,
        operator=operator,
    )

    response = _serialize_equipment(entity)
    response["activity"] = entry.activity
    response["service_event_id"] = (
        event.id if event is not None else None
    )
    response["status_input"] = entry.status
    return response


@router.get("")
def list_equipment(
    container=Depends(get_container),
):
    factory = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if factory is None:
        factory = RepositoryFactory.create()
        owns_factory = True

    try:
        rows = factory.equipment().get_all()
        return [
            _serialize_equipment(row)
            for row in rows
        ]
    finally:
        if owns_factory:
            factory.close()


@router.get("/{equipment_id}")
def get_equipment(
    equipment_id: str,
    container=Depends(get_container),
):
    factory = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if factory is None:
        factory = RepositoryFactory.create()
        owns_factory = True

    try:
        entity = factory.equipment().get_by_equipment_id(
            equipment_id
        )
        if entity is None:
            raise HTTPException(
                status_code=404,
                detail="Equipment not found",
            )

        return _serialize_equipment(entity)
    finally:
        if owns_factory:
            factory.close()


@router.patch("/{equipment_id}")
def update_equipment(
    equipment_id: str,
    entry: EquipmentPatchRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    operator = _operator(
        entry.model_dump(),
        current_user,
    )

    factory = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if factory is None:
        factory = RepositoryFactory.create()
        owns_factory = True

    try:
        repository = factory.equipment()
        entity = repository.get_by_equipment_id(
            equipment_id
        )

        if entity is None:
            raise HTTPException(
                status_code=404,
                detail="Equipment not found",
            )

        status = (
            _canonical_status(entry.status)
            if entry.status is not None
            else None
        )

        condition = (
            _canonical_condition(entry.condition)
            if entry.condition is not None
            else None
        )

        entity = repository.update(
            entity,
            name=entry.name,
            category=entry.category,
            location=entry.location,
            status=status,
            condition=condition,
            running_hours=entry.running_hours,
            commissioned_at=entry.commissioned_at,
            last_service_at=entry.last_service_at,
            next_service_due_at=(
                entry.next_service_due_at
            ),
            active=entry.active,
        )

        _publish_projection_event(
            container,
            equipment=entity,
            activity="master_update",
            operator=operator,
            notes=entry.notes,
        )

    finally:
        if owns_factory:
            factory.close()

    _raise_equipment_findings(
        entity,
        operator=operator,
    )

    return _serialize_equipment(entity)


@router.post("/{equipment_id}/service")
def record_equipment_service(
    equipment_id: str,
    entry: EquipmentServiceRequest,
    container=Depends(get_container),
    current_user: dict[str, Any] | None = Depends(
        get_optional_current_user
    ),
):
    payload = entry.model_dump()
    operator = _operator(payload, current_user)

    factory = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if factory is None:
        factory = RepositoryFactory.create()
        owns_factory = True

    try:
        repository = factory.equipment()
        entity = repository.get_by_equipment_id(
            equipment_id
        )

        if entity is None:
            raise HTTPException(
                status_code=404,
                detail="Equipment not found",
            )

        before_status = entity.status
        next_due = entry.next_service_due_at

        entity = repository.update(
            entity,
            running_hours=entry.running_hours,
            status=(
                _canonical_status(entry.status_after)
                if entry.status_after is not None
                else entity.status
            ),
            last_service_at=utcnow(),
            next_service_due_at=next_due,
        )

        event = repository.add_service_event(
            equipment_id=equipment_id,
            event_date=(
                entry.event_date
                or utcnow().date()
            ),
            event_type=entry.event_type,
            running_hours=entry.running_hours,
            status_before=before_status,
            status_after=entity.status,
            operator=operator,
            notes=entry.notes,
        )

        _publish_projection_event(
            container,
            equipment=entity,
            activity=entry.event_type,
            operator=operator,
            notes=entry.notes,
        )

    finally:
        if owns_factory:
            factory.close()

    _raise_equipment_findings(
        entity,
        operator=operator,
    )

    return {
        "equipment": _serialize_equipment(entity),
        "service_event": _serialize_service_event(event),
    }


@router.get("/{equipment_id}/service-history")
def equipment_service_history(
    equipment_id: str,
    container=Depends(get_container),
):
    factory = getattr(
        container,
        "repository_factory",
        None,
    )
    owns_factory = False

    if factory is None:
        factory = RepositoryFactory.create()
        owns_factory = True

    try:
        repository = factory.equipment()

        if repository.get_by_equipment_id(
            equipment_id
        ) is None:
            raise HTTPException(
                status_code=404,
                detail="Equipment not found",
            )

        return [
            _serialize_service_event(row)
            for row in repository.service_history(
                equipment_id
            )
        ]
    finally:
        if owns_factory:
            factory.close()
