from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.api.reference_data import GOVERNED


router = APIRouter()

# Reconciled 2026-08-14: validate against the same governed lists advertised
# at GET /farm/reference-data instead of keeping a separate literal set here
# (that drift — SOLD/DECEASED advertised but rejected, CLOSE_UP/SICK
# accepted but not advertised — is what this fixes). See
# dairyos.api.reference_data.GOVERNED for the single source of truth.
ALLOWED_LIFECYCLE_STATUSES = set(GOVERNED["lifecycle_statuses"])
ALLOWED_MILKING_FREQUENCIES = set(GOVERNED["milking_frequencies"])


def animal_repository(container):
    return container.animal_repository


def serialize_animal(animal):
    if animal is None:
        return None

    return {
        "id": animal.id,
        "animal_id": animal.animal_id,
        "animal_type": animal.animal_type,
        "ear_tag": animal.ear_tag,
        "rfid": animal.rfid,
        "breed": animal.breed,
        "sex": animal.sex,
        "date_of_birth": (
            animal.date_of_birth.isoformat()
            if animal.date_of_birth else None
        ),
        "dam_id": getattr(animal, "dam_id", None),
        "sire_id": getattr(animal, "sire_id", None),
        "lifecycle_status": animal.lifecycle_status,
        "status": animal.status,
        "is_currently_milking": animal.is_currently_milking,
        "milking_frequency": animal.milking_frequency,
        "production_group": animal.production_group,
        "location": animal.location,
        "active": animal.active,
        "created_at": (
            animal.created_at.isoformat()
            if animal.created_at else None
        ),
        "updated_at": (
            animal.updated_at.isoformat()
            if animal.updated_at else None
        ),
    }


def get_animal_record(container, animal_id):
    return animal_repository(container).get_by_animal_id(animal_id)


def _record_operational_event(container, input_type, payload, actor):
    gateway = getattr(container, "input_gateway", None)

    if gateway is not None:
        gateway.record(
            input_type=input_type,
            payload={
                **payload,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operator": actor,
            },
            actor=actor,
        )


@router.get("/animals")
def list_animals(
    currently_milking: bool = False,
    container=Depends(get_container),
):
    repository = animal_repository(container)

    animals = (
        repository.currently_milking_animals()
        if currently_milking
        else repository.get_all()
    )

    return [
        serialize_animal(animal)
        for animal in animals
    ]


@router.get("/animals/{animal_id}")
def get_animal(
    animal_id: str,
    container=Depends(get_container),
):
    animal = get_animal_record(container, animal_id)

    if not animal:
        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    return serialize_animal(animal)


@router.get("/animals/current/milking")
def list_milking_animals(
    container=Depends(get_container),
):
    return [
        serialize_animal(animal)
        for animal in animal_repository(
            container
        ).currently_milking_animals()
    ]


@router.patch("/animals/{animal_id}/lifecycle")
def change_lifecycle(
    animal_id: str,
    payload: dict,
    container=Depends(get_container),
):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)

    if not animal:
        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    lifecycle = str(
        payload.get("lifecycle_status", "")
    ).upper()

    if lifecycle not in ALLOWED_LIFECYCLE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid lifecycle status. "
                "Allowed: "
                + ", ".join(sorted(ALLOWED_LIFECYCLE_STATUSES))
            ),
        )

    previous = animal.lifecycle_status

    animal.lifecycle_status = lifecycle
    animal.status = payload.get(
        "status",
        lifecycle,
    )
    animal.production_group = payload.get(
        "production_group",
        getattr(animal, "production_group", None),
    )
    animal.is_currently_milking = (
        lifecycle == "LACTATING"
    )
    animal.updated_at = datetime.now(timezone.utc)

    updated = repository.save(animal)

    _record_operational_event(
        container,
        "animal_lifecycle",
        {
            "animal_id": animal_id,
            "previous_status": previous,
            "lifecycle_status": lifecycle,
            "reason": payload.get("reason"),
        },
        str(payload.get("operator") or "API"),
    )

    return serialize_animal(updated)


@router.post("/animals/{animal_id}/milking-frequency")
def change_milking_frequency(
    animal_id: str,
    payload: dict,
    container=Depends(get_container),
):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)

    if not animal:
        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    frequency = payload.get("milking_frequency")

    if frequency not in ALLOWED_MILKING_FREQUENCIES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid milking frequency. Allowed: "
                + ", ".join(sorted(ALLOWED_MILKING_FREQUENCIES))
            ),
        )

    try:
        updated = repository.set_milking_frequency(
            animal_id=animal_id,
            new_frequency=frequency,
            changed_by=payload.get("changed_by"),
            reason=payload.get("reason"),
            effective_date=payload.get("effective_date"),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return serialize_animal(updated)


@router.get(
    "/animals/{animal_id}/milking-frequency/history"
)
def milking_frequency_history(
    animal_id: str,
    container=Depends(get_container),
):
    repository = animal_repository(container)
    animal = repository.get_by_animal_id(animal_id)

    if not animal:
        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    return [
        {
            "milking_frequency": record.milking_frequency,
            "changed_by": record.changed_by,
            "reason": record.reason,
            "effective_from": (
                record.effective_from.isoformat()
                if record.effective_from else None
            ),
            "effective_to": (
                record.effective_to.isoformat()
                if record.effective_to else None
            ),
        }
        for record in repository.get_milking_frequency_history(
            animal_id
        )
    ]


@router.post("/animals/{animal_id}/vaccinations")
def record_vaccination(
    animal_id: str,
    payload: dict,
    container=Depends(get_container),
):
    animal = get_animal_record(container, animal_id)

    if not animal:
        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    vaccine = str(
        payload.get("vaccine")
        or payload.get("vaccination")
        or ""
    ).strip()

    if not vaccine:
        raise HTTPException(
            status_code=422,
            detail="vaccine required",
        )

    administered = (
        payload.get("administered_date")
        or datetime.now(timezone.utc).date().isoformat()
    )

    record = {
        "animal_id": animal_id,
        "vaccine": vaccine,
        "dose": payload.get("dose"),
        "administered_date": administered,
        "next_due_date": payload.get(
            "next_due_date"
        ),
        "batch_number": payload.get(
            "batch_number"
        ),
        "veterinarian": payload.get(
            "veterinarian"
        ),
        "notes": payload.get("notes"),
        "status": "COMPLETED",
    }

    _record_operational_event(
        container,
        "vaccination",
        record,
        str(payload.get("operator") or "API"),
    )

    return record


@router.get("/animals/{animal_id}/vaccinations")
def list_vaccinations(
    animal_id: str,
    container=Depends(get_container),
):
    animal = get_animal_record(container, animal_id)

    if not animal:
        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    records = []

    for event in container.event_journal.all_events():
        if (
            event.name == "OperationalInputReceived"
            and event.payload.get("input_type")
            == "vaccination"
            and str(
                event.payload.get("animal_id")
            ) == animal_id
        ):
            records.append(event.payload)

    return records
