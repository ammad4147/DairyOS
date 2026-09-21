from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.api.operational_write import operational_write
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)

router = APIRouter(prefix="/farm/youngstock", tags=["Calf & Youngstock Management"])

YOUNGSTOCK_STATUSES = {"CALF", "HEIFER", "CLOSE_UP"}
BODY_DEVELOPMENT_STATUSES = YOUNGSTOCK_STATUSES | {
    "LACTATING", "MILKING", "DRY", "BULL", "ACTIVE", "OPEN",
}
GROWTH_EVENT = "youngstock_growth"
WEANING_EVENT = "youngstock_weaning"
CARE_EVENT = "youngstock_care"
CARE_TYPES = {
    "FIRST_COLOSTRUM": "First colostrum recorded",
    "NAVEL_CARE": "Navel care recorded",
}


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


def _serialize(animal, growth: list[dict[str, Any]], weaning: list[dict[str, Any]], care: list[dict[str, Any]] | None = None):
    today = OperationalDateAuthority().current_date()
    age_days = None
    newborn_context = False
    if animal.date_of_birth:
        created_at = getattr(animal, "created_at", None)
        created_day = created_at.date() if hasattr(created_at, "date") else created_at
        newborn_context = created_day is None or (created_day - animal.date_of_birth).days <= 7
        age_days = max(0, (today - animal.date_of_birth).days)

    latest_growth = growth[-1] if growth else None
    latest_weaning = weaning[-1] if weaning else None
    care = care or []
    birth_weight = None
    if animal.date_of_birth and newborn_context:
        birth_day = animal.date_of_birth.isoformat()
        birth_records = [row for row in growth if str(row.get("measured_at")) == birth_day]
        if birth_records:
            birth_weight = birth_records[-1].get("weight_kg")

    def _days_between(start: Any, end: Any) -> int | None:
        try:
            return (date.fromisoformat(str(end)) - date.fromisoformat(str(start))).days
        except (TypeError, ValueError):
            return None

    total_gain = None
    birth_to_current_adg = None
    if birth_weight is not None and latest_growth and animal.date_of_birth:
        total_gain = round(float(latest_growth["weight_kg"]) - float(birth_weight), 3)
        days = _days_between(animal.date_of_birth, latest_growth.get("measured_at"))
        if days and days > 0:
            birth_to_current_adg = round(total_gain / days, 3)

    age_at_weaning_days = None
    birth_to_weaning_adg = None
    if latest_weaning and animal.date_of_birth:
        age_at_weaning_days = _days_between(animal.date_of_birth, latest_weaning.get("weaned_at"))
        if age_at_weaning_days and age_at_weaning_days > 0 and birth_weight is not None and latest_weaning.get("weight_kg") is not None:
            birth_to_weaning_adg = round(
                (float(latest_weaning["weight_kg"]) - float(birth_weight)) / age_at_weaning_days,
                3,
            )

    checklist = [
        {
            "key": "birth_weight",
            "label": "Birth weight recorded",
            "status": "COMPLETE" if birth_weight is not None else "NOT_RECORDED",
            "evidence": "youngstock_growth" if birth_weight is not None else None,
        },
        {
            "key": "growth_measurement",
            "label": "Current growth measurement recorded",
            "status": "COMPLETE" if latest_growth is not None else "NOT_RECORDED",
            "evidence": "youngstock_growth" if latest_growth is not None else None,
        },
        {
            "key": "weaning",
            "label": "Weaning recorded",
            "status": "COMPLETE" if latest_weaning is not None else "NOT_RECORDED",
            "evidence": "youngstock_weaning" if latest_weaning is not None else None,
        },
    ]
    if animal.date_of_birth and newborn_context:
        now = OperationalDateAuthority().current_date()
        age_days = max(0, (now - animal.date_of_birth).days)
        for care_type, label in CARE_TYPES.items():
            evidence = next((row for row in care if row.get("care_type") == care_type), None)
            due_days = 0 if care_type == "FIRST_COLOSTRUM" else 1
            if evidence:
                completed = _parse_business_date(evidence.get("completed_at"), "completed_at")
                status = "COMPLETED_LATE" if completed > animal.date_of_birth and (completed - animal.date_of_birth).days > due_days else "COMPLETE"
            elif age_days > due_days:
                status = "OVERDUE"
            else:
                status = "DUE"
            checklist.append({"key": care_type.lower(), "label": label, "status": status, "evidence": CARE_EVENT if evidence else None})
    elif animal.date_of_birth:
        checklist.append({"key": "newborn_care", "label": "Newborn-care history", "status": "HISTORICAL_CONTEXT_REQUIRED", "evidence": None})
    else:
        checklist.append({"key": "newborn_care", "label": "Newborn-care history", "status": "HISTORICAL_CONTEXT_REQUIRED", "evidence": None})
    warnings = [
        {
            "warning_id": f"CALF-{animal.animal_id}-{item['key']}",
            "dedupe_key": f"CALF_MANAGEMENT:{animal.animal_id}:{item['key']}",
            "subject_id": animal.animal_id,
            "title": item["label"],
            "status": item["status"],
            "severity": "HIGH" if item["status"] == "OVERDUE" and item["key"] == "first_colostrum" else "MONITORING",
            "route": f"/farm/animals/{animal.animal_id}/passport",
        }
        for item in checklist
        if item["status"] in {"DUE", "OVERDUE"}
    ]
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
        "body_development": {
            "birth_weight_kg": birth_weight,
            "latest_weight_kg": latest_growth.get("weight_kg") if latest_growth else None,
            "total_gain_kg": total_gain,
            "birth_to_current_adg_kg_day": birth_to_current_adg,
            "body_condition_score": latest_growth.get("body_condition_score") if latest_growth else None,
            "measurement_count": len(growth),
        },
        "weaning_summary": {
            "weaned": latest_weaning is not None,
            "age_at_weaning_days": age_at_weaning_days,
            "weight_at_weaning_kg": latest_weaning.get("weight_kg") if latest_weaning else None,
            "birth_to_weaning_adg_kg_day": birth_to_weaning_adg,
        },
        "management_checklist": checklist,
        "care_records": care,
        "management_warnings": warnings,
    }


def _record(container, input_type: str, payload: dict[str, Any], operator: str):
    canonical = {
        **payload,
        "input_type": input_type,
        "operator": operator,
        "timestamp": payload.get("timestamp") or datetime.now(UTC).isoformat(),
    }
    event = container.input_gateway.record(
        input_type=input_type,
        payload=canonical,
        actor=operator,
    )
    return {**canonical, **dict(getattr(event, "payload", {}) or {})}


def _parse_business_date(value: Any, field_name: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} must be an ISO date") from exc


def _validate_growth_payload(animal, payload: dict[str, Any], existing: list[dict[str, Any]]) -> dict[str, Any]:
    measured_at = payload.get("measured_at") or OperationalDateAuthority().current_date().isoformat()
    measured_date = _parse_business_date(measured_at, "measured_at")
    today = OperationalDateAuthority().current_date()
    if measured_date > today:
        raise HTTPException(status_code=422, detail="measured_at cannot be in the future")
    if animal.date_of_birth and measured_date < animal.date_of_birth:
        raise HTTPException(status_code=422, detail="measured_at cannot precede the animal birth date")

    try:
        weight_kg = float(payload.get("weight_kg"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="weight_kg must be a number") from exc
    if not 0 < weight_kg <= 1500:
        raise HTTPException(status_code=422, detail="weight_kg must be between 0 and 1500 kg")

    bcs = None
    if payload.get("body_condition_score") is not None:
        try:
            bcs = float(payload["body_condition_score"])
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="body_condition_score must be a number") from exc
        if not 1 <= bcs <= 5 or round(bcs * 4) != bcs * 4:
            raise HTTPException(status_code=422, detail="body_condition_score must be 1.0 to 5.0 in 0.25 steps")

    method = str(payload.get("measurement_method") or "SCALE").strip().upper()
    if method not in {"SCALE", "TAPE", "ESTIMATED", "OTHER"}:
        raise HTTPException(status_code=422, detail="measurement_method is not supported")
    if any(str(row.get("measured_at")) == measured_date.isoformat() and not row.get("superseded") for row in existing):
        raise HTTPException(status_code=409, detail="A growth measurement already exists for this date")

    return {
        "animal_id": animal.animal_id,
        "measured_at": measured_date.isoformat(),
        "weight_kg": weight_kg,
        "height_cm": float(payload["height_cm"]) if payload.get("height_cm") is not None else None,
        "body_condition_score": bcs,
        "measurement_method": method,
        "notes": payload.get("notes"),
    }


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
                _event_records(container, CARE_EVENT, animal.animal_id),
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
    if lifecycle not in BODY_DEVELOPMENT_STATUSES:
        raise HTTPException(status_code=409, detail="Body development is unavailable for inactive or exited animals")
    return _serialize(
        animal,
        _event_records(container, GROWTH_EVENT, animal_id),
        _event_records(container, WEANING_EVENT, animal_id),
        _event_records(container, CARE_EVENT, animal_id),
    )


@router.post("/{animal_id}/growth")
@operational_write
def record_growth(animal_id: str, payload: dict[str, Any], container=Depends(get_container)):
    animal = _animal(container, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    lifecycle = str(getattr(animal, "lifecycle_status", "") or "").upper()
    if lifecycle not in BODY_DEVELOPMENT_STATUSES:
        raise HTTPException(status_code=409, detail="Growth recording is unavailable for inactive or exited animals")

    record = _validate_growth_payload(
        animal,
        payload,
        _event_records(container, GROWTH_EVENT, animal_id),
    )
    return _record(container, GROWTH_EVENT, record, str(payload.get("operator") or "API"))


@router.post("/{animal_id}/weaning")
@operational_write
def record_weaning(animal_id: str, payload: dict[str, Any], container=Depends(get_container)):
    animal = _animal(container, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    lifecycle = str(getattr(animal, "lifecycle_status", "") or "").upper()
    if lifecycle != "CALF":
        raise HTTPException(status_code=409, detail="Weaning can only be recorded for a CALF")

    weaned_at = payload.get("weaned_at") or OperationalDateAuthority().current_date().isoformat()
    weaned_date = _parse_business_date(weaned_at, "weaned_at")
    today = OperationalDateAuthority().current_date()
    if weaned_date > today:
        raise HTTPException(status_code=422, detail="weaned_at cannot be in the future")
    if animal.date_of_birth and weaned_date < animal.date_of_birth:
        raise HTTPException(status_code=422, detail="weaned_at cannot precede the animal birth date")
    if _event_records(container, WEANING_EVENT, animal_id):
        raise HTTPException(status_code=409, detail="Weaning has already been recorded for this calf")
    record = {
        "animal_id": animal_id,
        "weaned_at": weaned_date.isoformat(),
        "method": payload.get("method") or "STANDARD",
        "starter_feed_kg_day": float(payload["starter_feed_kg_day"]) if payload.get("starter_feed_kg_day") is not None else None,
        "weight_kg": float(payload["weight_kg"]) if payload.get("weight_kg") is not None else None,
        "notes": payload.get("notes"),
    }
    return _record(container, WEANING_EVENT, record, str(payload.get("operator") or "API"))


@router.post("/{animal_id}/care")
@operational_write
def record_care(animal_id: str, payload: dict[str, Any], container=Depends(get_container)):
    animal = _animal(container, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    lifecycle = str(getattr(animal, "lifecycle_status", "") or "").upper()
    if lifecycle not in YOUNGSTOCK_STATUSES:
        raise HTTPException(status_code=409, detail="Newborn care is restricted to calf/youngstock")
    care_type = str(payload.get("care_type") or "").strip().upper()
    if care_type not in CARE_TYPES:
        raise HTTPException(status_code=422, detail="care_type must be FIRST_COLOSTRUM or NAVEL_CARE")
    completed_at = _parse_business_date(payload.get("completed_at") or OperationalDateAuthority().current_date().isoformat(), "completed_at")
    today = OperationalDateAuthority().current_date()
    if completed_at > today:
        raise HTTPException(status_code=422, detail="completed_at cannot be in the future")
    if animal.date_of_birth and completed_at < animal.date_of_birth:
        raise HTTPException(status_code=422, detail="completed_at cannot precede the animal birth date")
    existing = _event_records(container, CARE_EVENT, animal_id)
    if any(row.get("care_type") == care_type for row in existing):
        raise HTTPException(status_code=409, detail=f"{care_type} has already been recorded")
    return _record(container, CARE_EVENT, {
        "animal_id": animal_id,
        "care_type": care_type,
        "completed_at": completed_at.isoformat(),
        "quantity_liters": float(payload["quantity_liters"]) if payload.get("quantity_liters") is not None else None,
        "quality_brix": float(payload["quality_brix"]) if payload.get("quality_brix") is not None else None,
        "notes": payload.get("notes"),
    }, str(payload.get("operator") or "API"))


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
