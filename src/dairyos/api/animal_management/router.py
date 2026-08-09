from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from enum import Enum

from dairyos.api.dependencies import get_container
from dairyos.domain.commands import Command
from dairyos.data.models.animal import Animal


router = APIRouter()


class LifecycleStatus(str, Enum):

    CALF = "CALF"
    HEIFER = "HEIFER"
    LACTATING = "LACTATING"
    DRY = "DRY"


class MilkingFrequency(str, Enum):

    ONCE_DAILY = "ONCE_DAILY"
    TWICE_DAILY = "TWICE_DAILY"
    THRICE_DAILY = "THRICE_DAILY"


def animal_repository(
    container,
):

    return container.animal_repository


def serialize_animal(
    animal,
):

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
            if animal.date_of_birth
            else None
        ),
        "lifecycle_status":
            animal.lifecycle_status,
        "status":
            animal.status,
        "is_currently_milking":
            animal.is_currently_milking,
        "milking_frequency":
            animal.milking_frequency,
        "production_group":
            animal.production_group,
        "location":
            animal.location,
        "active":
            animal.active,
        "created_at": (
            animal.created_at.isoformat()
            if animal.created_at
            else None
        ),
        "updated_at": (
            animal.updated_at.isoformat()
            if animal.updated_at
            else None
        ),
    }


def get_animal_record(
    container,
    animal_id,
):

    return (
        animal_repository(container)
        .get_by_animal_id(animal_id)
    )


@router.post("/animals")
def create_animal(
    payload: dict,
    container=Depends(get_container),
):

    animal_id = payload.get(
        "animal_id"
    )

    if not animal_id:

        raise HTTPException(
            status_code=422,
            detail="animal_id required",
        )

    repository = animal_repository(
        container
    )

    if repository.exists(
        animal_id
    ):

        raise HTTPException(
            status_code=409,
            detail="Animal already exists",
        )

    lifecycle_status = payload.get(
        "lifecycle_status",
        "HEIFER",
    )

    try:

        LifecycleStatus(
            lifecycle_status
        )

    except ValueError:

        raise HTTPException(
            status_code=422,
            detail="Invalid lifecycle status",
        )

    allowed_fields = {
        "animal_id",
        "animal_type",
        "ear_tag",
        "rfid",
        "breed",
        "sex",
        "date_of_birth",
        "lifecycle_status",
        "status",
        "is_currently_milking",
        "milking_frequency",
        "production_group",
        "location",
        "active",
    }

    animal_payload = {
        key: value
        for key, value in payload.items()
        if key in allowed_fields
    }

    animal = Animal(
        **animal_payload
    )

    saved = repository.save(
        animal
    )

    if payload.get(
        "milking_frequency"
    ):

        repository.set_milking_frequency(
            animal_id=animal_id,
            new_frequency=payload[
                "milking_frequency"
            ],
            changed_by=None,
            reason="initial",
        )

        saved = repository.get_by_animal_id(
            animal_id
        )

    event_payload = {
        **payload,
        "active": True,
        "created_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    event = container.operations.handle_command(
        Command(
            name="CreateAnimal",
            payload=event_payload,
        )
    )

    if event:

        return serialize_animal(
            saved
        )

    return serialize_animal(
        saved
    )


@router.get("/animals")
def list_animals(
    currently_milking: bool = False,
    container=Depends(get_container),
):

    repository = animal_repository(
        container
    )

    if currently_milking:

        animals = (
            repository
            .currently_milking_animals()
        )

    else:

        animals = (
            repository
            .get_all()
        )

    return [
        serialize_animal(
            animal
        )
        for animal in animals
    ]


@router.get("/animals/{animal_id}")
def get_animal(
    animal_id: str,
    container=Depends(get_container),
):

    animal = get_animal_record(
        container,
        animal_id,
    )

    if not animal:

        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    return serialize_animal(
        animal
    )


@router.get("/animals/current/milking")
def list_milking_animals(
    container=Depends(get_container),
):

    repository = animal_repository(
        container
    )

    return [
        serialize_animal(
            animal
        )
        for animal in (
            repository
            .currently_milking_animals()
        )
    ]


@router.post(
    "/animals/{animal_id}/milking-frequency"
)
def change_milking_frequency(
    animal_id: str,
    payload: dict,
    container=Depends(get_container),
):

    repository = animal_repository(
        container
    )

    animal = repository.get_by_animal_id(
        animal_id
    )

    if not animal:

        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    frequency = payload.get(
        "milking_frequency"
    )

    try:

        MilkingFrequency(
            frequency
        )

    except ValueError:

        raise HTTPException(
            status_code=422,
            detail="Invalid milking frequency",
        )

    updated = repository.set_milking_frequency(
        animal_id=animal_id,
        new_frequency=frequency,
        changed_by=payload.get(
            "changed_by"
        ),
        reason=payload.get(
            "reason"
        ),
    )

    return serialize_animal(
        updated
    )


@router.get(
    "/animals/{animal_id}/milking-frequency/history"
)
def milking_frequency_history(
    animal_id: str,
    container=Depends(get_container),
):

    repository = animal_repository(
        container
    )

    animal = repository.get_by_animal_id(
        animal_id
    )

    if not animal:

        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    history = (
        repository
        .get_milking_frequency_history(
            animal_id
        )
    )

    return [
        {
            "milking_frequency":
                record.milking_frequency,

            "changed_by":
                record.changed_by,

            "reason":
                record.reason,

            "effective_from": (
                record.effective_from.isoformat()
                if record.effective_from
                else None
            ),

            "effective_to": (
                record.effective_to.isoformat()
                if record.effective_to
                else None
            ),
        }
        for record in history
    ]