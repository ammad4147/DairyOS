"""System-generated permanent animal registration endpoint.

The operator supplies animal attributes, but never the permanent Animal ID.
The ID is generated server-side before persistence and returned to the UI.
"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.api.reference_data import GOVERNED
from dairyos.domain.commands import Command


router = APIRouter(
    prefix="/farm/animals",
    tags=["Animal Registration"],
)


def _new_animal_id(repository) -> str:
    """Generate a collision-safe permanent identifier owned by DairyOS."""
    for _ in range(10):
        candidate = f"AN-{uuid4().hex.upper()}"
        if not repository.exists(candidate):
            return candidate
    raise HTTPException(
        status_code=500,
        detail="Unable to generate a unique permanent Animal ID",
    )


@router.post("")
def register_animal(
    payload: dict,
    container=Depends(get_container),
):
    """Create an animal without accepting a client-supplied Animal ID."""

    if payload.get("animal_id") is not None:
        raise HTTPException(
            status_code=400,
            detail="animal_id is system-generated and cannot be supplied by the operator",
        )

    animal_type = payload.get("animal_type")
    if not animal_type:
        raise HTTPException(status_code=422, detail="animal_type required")

    lifecycle_status = payload.get("lifecycle_status", "HEIFER")
    allowed_lifecycle = set(GOVERNED["lifecycle_statuses"])
    if lifecycle_status not in allowed_lifecycle:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid lifecycle status. Allowed: "
                + ", ".join(sorted(allowed_lifecycle))
            ),
        )

    milking_frequency = payload.get("milking_frequency")
    allowed_frequency = set(GOVERNED["milking_frequencies"])
    if milking_frequency and milking_frequency not in allowed_frequency:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid milking frequency. Allowed: "
                + ", ".join(sorted(allowed_frequency))
            ),
        )

    allowed_fields = {
        "animal_type",
        "ear_tag",
        "rfid",
        "breed",
        "sex",
        "date_of_birth",
        "dam_id",
        "sire_id",
        "lifecycle_status",
        "status",
        "is_currently_milking",
        "milking_frequency",
        "production_group",
        "location",
        "active",
    }

    repository = container.animal_repository
    animal_id = _new_animal_id(repository)

    animal_payload = {
        key: value
        for key, value in payload.items()
        if key in allowed_fields
    }
    animal_payload["animal_id"] = animal_id
    animal_payload["lifecycle_status"] = lifecycle_status
    animal_payload["active"] = True

    animal_model = __import__(
        "dairyos.data.models.animal",
        fromlist=["Animal"],
    ).Animal

    animal = repository.save(animal_model(**animal_payload))

    if payload.get("milking_frequency"):
        repository.set_milking_frequency(
            animal_id=animal_id,
            new_frequency=payload["milking_frequency"],
            changed_by=None,
            reason="initial",
        )
        animal = repository.get_by_animal_id(animal_id)

    try:
        container.operations.handle_command(
            Command(
                name="CreateAnimal",
                payload={
                    **animal_payload,
                    "active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "system_generated_animal_id": True,
                },
            )
        )
    except Exception:
        # Persistence above is authoritative. Command projection is ancillary.
        pass

    return {
        "id": animal.id,
        "animal_id": animal.animal_id,
        "system_generated_animal_id": True,
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
