"""Milk traceability projection from persisted animal, milk and operational records."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container

router = APIRouter(prefix="/farm/milk", tags=["Milk Traceability"])


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


@router.get("/{animal_id}/traceability")
def animal_milk_traceability(animal_id: str, container=Depends(get_container)):
    animal = container.animal_repository.get_by_animal_id(animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")

    milk_records = [
        record for record in container.milk_repository.get_all()
        if str(record.animal_id) == animal_id
    ]

    operational_events = []
    for event in container.operational_event_repository.get_all():
        description = str(getattr(event, "description", ""))
        if "milk_production" in description and (
            f"entity_id={animal_id}" in description
            or f"animal_id={animal_id}" in description
        ):
            operational_events.append({
                "id": getattr(event, "id", None),
                "event_type": getattr(event, "event_type", None),
                "source": getattr(event, "source", None),
                "description": description,
                "created_at": _iso(getattr(event, "created_at", None)),
            })

    sessions = []
    for event in operational_events:
        sessions.append(event)

    total_litres = sum(float(record.total_yield or 0) for record in milk_records)
    return {
        "data_status": "LIVE_PERSISTED",
        "animal": {
            "animal_id": animal.animal_id,
            "ear_tag": animal.ear_tag,
            "breed": animal.breed,
            "lifecycle_status": animal.lifecycle_status,
        },
        "milk_records": [
            {
                "id": record.id,
                "animal_id": record.animal_id,
                "production_date": _iso(record.production_date),
                "morning_yield": record.morning_yield,
                "afternoon_yield": record.afternoon_yield,
                "evening_yield": record.evening_yield,
                "total_yield": record.total_yield,
                "status": record.status,
            }
            for record in milk_records
        ],
        "operational_trace": sessions,
        "record_count": len(milk_records),
        "total_litres": total_litres,
        "traceability_complete": all(
            str(record.animal_id) == animal_id for record in milk_records
        ),
    }
