"""Lifetime Animal Passport projection over persisted operational records."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory

router = APIRouter(prefix="/farm/animals", tags=["Animal Passport"])


def _for_animal(records, animal_id: str):
    return [
        record
        for record in records
        if str(getattr(record, "animal_id", "")) == animal_id
    ]


def _serialize(record):
    if hasattr(record, "__dict__"):
        values = {
            key: value
            for key, value in vars(record).items()
            if not key.startswith("_")
        }
    elif isinstance(record, dict):
        values = dict(record)
    else:
        values = {"value": str(record)}

    for key, value in list(values.items()):
        if hasattr(value, "isoformat"):
            values[key] = value.isoformat()
    return values


@router.get("/{animal_id}/passport")
def get_lifetime_passport(
    animal_id: str,
    container=Depends(get_container),
):
    """Return animal identity plus current persisted cross-domain lifetime history.

    The passport is a read model over durable operational repositories.  It
    deliberately opens a fresh repository session for the projection rather
    than reading long-lived runtime repository instances.  Operational writes
    may be committed through separate repository sessions, so the passport
    must observe the committed database state immediately after those writes.
    """
    factory = RepositoryFactory.create()
    try:
        animal_repo = factory.animal()
        animal = animal_repo.get_by_animal_id(animal_id)
        if animal is None:
            raise HTTPException(status_code=404, detail="Animal not found")

        milk = _for_animal(factory.milk().get_all(), animal_id)
        health = _for_animal(factory.health().get_all(), animal_id)
        breeding = _for_animal(factory.breeding().get_all(), animal_id)
        treatments = factory.treatment().get_by_animal(animal_id)

        events = []
        for event in factory.operational_events().get_all():
            description = str(getattr(event, "description", ""))
            if f"entity_id={animal_id}" in description or f"animal_id={animal_id}" in description:
                events.append(_serialize(event))

        return {
            "animal": {
                "id": animal.id,
                "animal_id": animal.animal_id,
                "animal_type": animal.animal_type,
                "ear_tag": animal.ear_tag,
                "rfid": animal.rfid,
                "breed": animal.breed,
                "sex": animal.sex,
                "date_of_birth": animal.date_of_birth.isoformat() if animal.date_of_birth else None,
                "dam_id": getattr(animal, "dam_id", None),
                "sire_id": getattr(animal, "sire_id", None),
                "lifecycle_status": animal.lifecycle_status,
                "status": animal.status,
                "active": animal.active,
                "created_at": animal.created_at.isoformat() if animal.created_at else None,
                "updated_at": animal.updated_at.isoformat() if animal.updated_at else None,
            },
            "history": {
                "milk": [_serialize(item) for item in milk],
                "health": [_serialize(item) for item in health],
                "breeding": [_serialize(item) for item in breeding],
                "treatments": [_serialize(item) for item in treatments],
                "operational_events": events,
            },
            "record_counts": {
                "milk": len(milk),
                "health": len(health),
                "breeding": len(breeding),
                "treatments": len(treatments),
                "operational_events": len(events),
            },
        }
    finally:
        factory.close()
