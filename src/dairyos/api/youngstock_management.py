from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
from dairyos.data.repositories.repository_factory import RepositoryFactory


router = APIRouter(prefix="/farm/youngstock", tags=["Calf & Youngstock Management"])

YOUNGSTOCK_STATUSES = {"CALF", "HEIFER", "CLOSE_UP"}
GROWTH_EVENT = "youngstock_growth"
WEANING_EVENT = "youngstock_weaning"


def _animal(container, animal_id: str):
    return container.animal_repository.get_by_animal_id(animal_id)


def _event_records(container, input_type: str, animal_id: str | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for event in container.event_journal.all_events():
        if event.name != "OperationalInputReceived":
            continue
        payload = dict(event.payload or {})
        if payload.get("input_type") != input_type:
            continue
        if animal_id is not None and str(payload.get("animal_id")) != animal_id:
            continue
        records.append(payload)
    records.sort(key=lambda row: str(row.get("timestamp") or ""))
    return records


def _youngstock_animals(container):
    return [
        animal
        for animal in container.animal_repository.get_all()
        if str(getattr(animal, "lifecycle_status", "") or "").upper() in YOUNGSTOCK_STATUSES
    ]


def _serialize(animal, growth: list[dict[str, Any]], weaning: list[dict[str, Any]]):
    today = OperationalDateAuthority().current_date()
    age_days = None
    if animal.date_of_birth:
        age_days = max(0, (today - animal.date_of_birth).days)

    latest_growth = growth[-1] if growth else None
    latest_weaning = weaning[-1] if weaning else None
    return {
        "animal_id": animal.animal_id,
        "animal_type": animal.animal_type,
        "sex": animal.sex,
        "breed": animal.breed,
        "date_of_birth": animal.date_of_birth.isoformat() if animal.date_of_birth else None,
        "age_days": age_days,
        "dam_id": getattr(animal, "dam_id", None),
        "sire_id": getattr(animal, "sire_id", None),
        "lifecycle_status": animal.lifecycle_status,
        "production_group": animal.production_group,
        "location": animal.location,
        "active": animal.active,
        "growth_records": growth,
        "latest_growth": latest_growth,
        "weaning_records": weaning,
        "latest_weaning": latest_weaning,
    }


def _record(container, input_type: str, payload: dict[str, Any], operator: str):
    canonical = {
        **payload,
        "input_type": input_type,
        "operator": operator,
        "timestamp": payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    }
    event = container.input_gateway.record(
        input_type=input_type,
        payload=canonical,
        actor=operator,
    )
    return {**canonical, **dict(getattr(event, "payload", {}) or {})}


@router.get("/overview")
def youngstock_overview(container=Depends(get_container)):
    animals = _youngstock_animals(container)
    records = []
    for animal in animals:
        records.append(
            _serialize(
                animal,
                _event_records(container, GROWTH_EVENT, animal.animal_id),
                _event_records(container, WEANING_EVENT, animal.animal_id),
            )
        )

    return {
        "data_status": "LIVE_PERSISTED_DATA" if records else "NO_DATA",
        "youngstock_count": len(records),
        "calf_count": sum(1 for row in records if row["lifecycle_status"] == "CALF"),
        "heifer_count": sum(1 for row in records if row["lifecycle_status"] == "HEIFER"),
        "close_up_count": sum(1 for row in records if row["lifecycle_status"] == "CLOSE_UP"),
        "animals": records,
    }


@router.get("/{animal_id}")
def youngstock_profile(animal_id: str, container=Depends(get_container)):
    animal = _animal(container, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    lifecycle = str(getattr(animal, "lifecycle_status", "") or "").upper()
    if lifecycle not in YOUNGSTOCK_STATUSES:
        raise HTTPException(status_code=409, detail="Animal is not currently classified as calf/youngstock")
    return _serialize(
        animal,
        _event_records(container, GROWTH_EVENT, animal_id),
        _event_records(container, WEANING_EVENT, animal_id),
    )


@router.post("/{animal_id}/growth")
def record_growth(animal_id: str, payload: dict[str, Any], container=Depends(get_container)):
    animal = _animal(container, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    lifecycle = str(getattr(animal, "lifecycle_status", "") or "").upper()
    if lifecycle not in YOUNGSTOCK_STATUSES:
        raise HTTPException(status_code=409, detail="Growth recording is restricted to calf/youngstock")

    measured_at = payload.get("measured_at") or OperationalDateAuthority().current_date().isoformat()
    weight_kg = payload.get("weight_kg")
    if weight_kg is None or float(weight_kg) <= 0:
        raise HTTPException(status_code=422, detail="weight_kg must be greater than zero")

    record = {
        "animal_id": animal_id,
        "measured_at": measured_at,
        "weight_kg": float(weight_kg),
        "height_cm": float(payload["height_cm"]) if payload.get("height_cm") is not None else None,
        "body_condition_score": float(payload["body_condition_score"]) if payload.get("body_condition_score") is not None else None,
        "notes": payload.get("notes"),
    }
    return _record(container, GROWTH_EVENT, record, str(payload.get("operator") or "API"))


@router.post("/{animal_id}/weaning")
def record_weaning(animal_id: str, payload: dict[str, Any], container=Depends(get_container)):
    animal = _animal(container, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    lifecycle = str(getattr(animal, "lifecycle_status", "") or "").upper()
    if lifecycle != "CALF":
        raise HTTPException(status_code=409, detail="Weaning can only be recorded for a CALF")

    weaned_at = payload.get("weaned_at") or OperationalDateAuthority().current_date().isoformat()
    record = {
        "animal_id": animal_id,
        "weaned_at": weaned_at,
        "method": payload.get("method") or "STANDARD",
        "starter_feed_kg_day": float(payload["starter_feed_kg_day"]) if payload.get("starter_feed_kg_day") is not None else None,
        "weight_kg": float(payload["weight_kg"]) if payload.get("weight_kg") is not None else None,
        "notes": payload.get("notes"),
    }
    return _record(container, WEANING_EVENT, record, str(payload.get("operator") or "API"))


@router.get("/{animal_id}/growth")
def growth_history(animal_id: str, container=Depends(get_container)):
    animal = _animal(container, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    return _event_records(container, GROWTH_EVENT, animal_id)


@router.get("/{animal_id}/weaning")
def weaning_history(animal_id: str, container=Depends(get_container)):
    animal = _animal(container, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    return _event_records(container, WEANING_EVENT, animal_id)

