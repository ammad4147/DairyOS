from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.api.reference_data import GOVERNED
from dairyos.farm.herd.services.animal_classification_service import (
    AnimalClassificationError,
    AnimalClassificationService,
)

router = APIRouter()

ALLOWED_LIFECYCLE_STATUSES = set(GOVERNED["lifecycle_statuses"])
ALLOWED_MILKING_FREQUENCIES = set(GOVERNED["milking_frequencies"])
EXIT_STATUSES = {"SOLD", "DECEASED"}


def animal_repository(container):
    return container.animal_repository


def serialize_animal(animal):
    if animal is None:
        return None
    result = {
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
        "is_currently_milking": animal.is_currently_milking,
        "milking_frequency": animal.milking_frequency,
        "production_group": animal.production_group,
        "location": animal.location,
        "active": animal.active,
        "created_at": animal.created_at.isoformat() if animal.created_at else None,
        "updated_at": animal.updated_at.isoformat() if animal.updated_at else None,
    }
    try:
        classification = AnimalClassificationService.classify(
            result.get("lifecycle_status"), result.get("sex")
        )
        result["sex"] = classification.sex
        result["lifecycle_status"] = classification.lifecycle_status
        result["animal_category"] = classification.category.value
    except AnimalClassificationError:
        result["animal_category"] = None
    return result


def get_animal_record(container, animal_id):
    return animal_repository(container).get_by_animal_id(animal_id)


def _record_operational_event(container, input_type, payload, actor):
    gateway = getattr(container, "input_gateway", None)
    if gateway is not None:
        gateway.record(
            input_type=input_type,
            payload={**payload, "timestamp": datetime.now(timezone.utc).isoformat(), "operator": actor},
            actor=actor,
        )


def _event_payloads_for_animal(container, input_type, animal_id):
    records = []
    for event in container.event_journal.all_events():
        if (
            event.name == "OperationalInputReceived"
            and event.payload.get("input_type") == input_type
            and str(event.payload.get("animal_id")) == animal_id
        ):
            records.append(event.payload)
    return records


def _apply_classification_payload(animal, payload):
    try:
        if "animal_category" in payload or "category" in payload:
            classification = AnimalClassificationService.from_category(
                str(payload.get("animal_category") or payload.get("category")),
                current_lifecycle=payload.get("lifecycle_status") or animal.lifecycle_status,
            )
            animal.sex = classification.sex
            animal.lifecycle_status = classification.lifecycle_status
            animal.is_currently_milking = classification.lifecycle_status == "LACTATING"
            return classification

        lifecycle = payload.get("lifecycle_status", animal.lifecycle_status)
        sex = payload.get("sex", animal.sex)
        classification = AnimalClassificationService.classify(lifecycle, sex)
        animal.sex = classification.sex
        animal.lifecycle_status = classification.lifecycle_status
        animal.is_currently_milking = classification.lifecycle_status == "LACTATING"
        return classification
    except AnimalClassificationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/animals")
def list_animals(currently_milking: bool = False, active_only: bool = False, container=Depends(get_container)):
    repository = animal_repository(container)
    if currently_milking:
        animals = repository.currently_milking_animals()
    elif active_only:
        animals = repository.active_animals()
    else:
        animals = repository.get_all()
    return [serialize_animal(animal) for animal in animals]


@router.get("/animals/current/milking")
def list_currently_milking_animals(container=Depends(get_container)):
    repository = animal_repository(container)
    return [serialize_animal(animal) for animal in repository.currently_milking_animals()]


@router.get("/animals/{animal_id}")
def get_animal(animal_id: str, container=Depends(get_container)):
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return serialize_animal(animal)


@router.patch("/animals/{animal_id}")
def update_animal(animal_id: str, payload: dict, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    if "animal_category" in payload or "category" in payload or "lifecycle_status" in payload or "sex" in payload:
        _apply_classification_payload(animal, payload)

    if "milking_frequency" in payload and payload.get("milking_frequency"):
        frequency = payload["milking_frequency"]
        if frequency not in ALLOWED_MILKING_FREQUENCIES:
            raise HTTPException(status_code=422, detail="Invalid milking frequency. Allowed: " + ", ".join(sorted(ALLOWED_MILKING_FREQUENCIES)))
        try:
            updated = repository.set_milking_frequency(
                animal_id=animal_id,
                new_frequency=frequency,
                changed_by=payload.get("changed_by") or payload.get("operator") or "API",
                reason=payload.get("milking_frequency_reason") or payload.get("reason"),
                effective_date=payload.get("effective_date"),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        animal = updated or animal

    editable_fields = {"animal_type", "ear_tag", "rfid", "breed", "sex", "date_of_birth", "dam_id", "sire_id", "production_group", "location"}
    changed = {}
    for field in editable_fields:
        if field in payload:
            setattr(animal, field, payload[field])
            changed[field] = payload[field]

    if "status" in payload and payload.get("status"):
        animal.status = str(payload["status"]).upper()
        changed["status"] = animal.status

    if "animal_category" in payload or "category" in payload or "lifecycle_status" in payload or "sex" in payload:
        changed["animal_category"] = serialize_animal(animal).get("animal_category")
        changed["lifecycle_status"] = animal.lifecycle_status
        changed["sex"] = animal.sex

    animal.updated_at = datetime.now(timezone.utc)
    updated = repository.save(animal)
    _record_operational_event(container, "animal_profile_update", {"animal_id": animal_id, "changed_fields": sorted(changed.keys())}, str(payload.get("operator") or "API"))
    return serialize_animal(updated)


@router.patch("/animals/{animal_id}/disposition")
def record_animal_disposition(animal_id: str, payload: dict, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    disposition = str(payload.get("disposition") or "").upper()
    if disposition not in EXIT_STATUSES:
        raise HTTPException(status_code=422, detail="Disposition must be SOLD or DECEASED")

    effective_date = str(payload.get("effective_date") or datetime.now(timezone.utc).date().isoformat())
    try:
        datetime.fromisoformat(effective_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="effective_date must be an ISO date") from exc

    animal.lifecycle_status = disposition
    animal.status = disposition
    animal.is_currently_milking = False
    animal.active = False
    animal.updated_at = datetime.now(timezone.utc)
    updated = repository.save(animal)

    event_payload = {
        "animal_id": animal_id,
        "disposition": disposition,
        "effective_date": effective_date,
        "reason": payload.get("reason"),
        "buyer_or_counterparty": payload.get("buyer_or_counterparty"),
        "amount": payload.get("amount"),
        "reference": payload.get("reference"),
        "veterinarian": payload.get("veterinarian"),
        "cause": payload.get("cause"),
        "notes": payload.get("notes"),
    }
    _record_operational_event(container, "animal_disposition", event_payload, str(payload.get("operator") or "API"))
    return {"animal": serialize_animal(updated), "disposition": event_payload}


@router.get("/animals/{animal_id}/disposition-history")
def disposition_history(animal_id: str, container=Depends(get_container)):
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return _event_payloads_for_animal(container, "animal_disposition", animal_id)


@router.post("/animals/{animal_id}/activate")
def activate_animal(animal_id: str, payload: dict | None = None, container=Depends(get_container)):
    payload = payload or {}
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    animal.activate()
    updated = repository.save(animal)
    _record_operational_event(container, "animal_activated", {"animal_id": animal_id, "reason": payload.get("reason")}, str(payload.get("operator") or "API"))
    return serialize_animal(updated)


@router.patch("/animals/{animal_id}/lifecycle")
def change_lifecycle(animal_id: str, payload: dict, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    lifecycle = str(payload.get("lifecycle_status", "")).upper()
    if lifecycle not in ALLOWED_LIFECYCLE_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid lifecycle status. Allowed: " + ", ".join(sorted(ALLOWED_LIFECYCLE_STATUSES)))
    previous = animal.lifecycle_status
    try:
        classification = AnimalClassificationService.classify(lifecycle, animal.sex)
    except AnimalClassificationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    animal.lifecycle_status = classification.lifecycle_status
    animal.sex = classification.sex
    animal.status = payload.get("status", classification.lifecycle_status)
    animal.production_group = payload.get("production_group", getattr(animal, "production_group", None))
    animal.is_currently_milking = classification.lifecycle_status == "LACTATING"
    animal.updated_at = datetime.now(timezone.utc)
    updated = repository.save(animal)
    _record_operational_event(container, "animal_lifecycle", {"animal_id": animal_id, "previous_status": previous, "lifecycle_status": classification.lifecycle_status, "reason": payload.get("reason")}, str(payload.get("operator") or "API"))
    return serialize_animal(updated)


@router.post("/animals/{animal_id}/milking-frequency")
def change_milking_frequency(animal_id: str, payload: dict, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    frequency = payload.get("milking_frequency")
    if frequency not in ALLOWED_MILKING_FREQUENCIES:
        raise HTTPException(status_code=422, detail="Invalid milking frequency. Allowed: " + ", ".join(sorted(ALLOWED_MILKING_FREQUENCIES)))
    try:
        updated = repository.set_milking_frequency(animal_id=animal_id, new_frequency=frequency, changed_by=payload.get("changed_by"), reason=payload.get("reason"), effective_date=payload.get("effective_date"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return serialize_animal(updated)


@router.get("/animals/{animal_id}/milking-frequency/history")
def milking_frequency_history(animal_id: str, container=Depends(get_container)):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return [{"milking_frequency": record.milking_frequency, "changed_by": record.changed_by, "reason": record.reason, "effective_from": record.effective_from.isoformat() if record.effective_from else None, "effective_to": record.effective_to.isoformat() if record.effective_to else None} for record in repository.get_milking_frequency_history(animal_id)]


@router.post("/animals/{animal_id}/vaccinations")
def record_vaccination(animal_id: str, payload: dict, container=Depends(get_container)):
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    vaccine = str(payload.get("vaccine") or payload.get("vaccination") or "").strip()
    if not vaccine:
        raise HTTPException(status_code=422, detail="vaccine required")
    administered = payload.get("administered_date") or datetime.now(timezone.utc).date().isoformat()
    record = {"animal_id": animal_id, "vaccine": vaccine, "dose": payload.get("dose"), "administered_date": administered, "next_due_date": payload.get("next_due_date"), "batch_number": payload.get("batch_number"), "veterinarian": payload.get("veterinarian"), "notes": payload.get("notes"), "status": "COMPLETED"}
    _record_operational_event(container, "vaccination", record, str(payload.get("operator") or "API"))
    return record


@router.get("/animals/{animal_id}/vaccinations")
def list_vaccinations(animal_id: str, container=Depends(get_container)):
    animal = get_animal_record(container, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return _event_payloads_for_animal(container, "vaccination", animal_id)
