from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.api.animals import _as_dict, _repository, _repository_call, _runtime

router = APIRouter(
    prefix="/farm/animals",
    tags=["animal-operational-entry"],
)


class AnimalRecordEntry(BaseModel):
    model_config = {"extra": "allow"}

    animal_id: str = Field(min_length=1)


def _require_animal(animal_id: str) -> dict:
    repository = _repository(_runtime())

    if repository is None:
        raise HTTPException(
            status_code=503,
            detail="Authoritative animal repository is not available",
        )

    animal = _repository_call(
        repository,
        (
            "get_by_animal_id",
            "get_by_id",
            "find_by_animal_id",
            "find_by_id",
            "find",
        ),
        animal_id,
    )

    if animal is None:
        raise HTTPException(
            status_code=404,
            detail=f"Animal not found: {animal_id}",
        )

    return _as_dict(animal)


def _persist(
    animal_id: str,
    payload: dict,
    methods: tuple[str, ...],
) -> dict:
    repository = _repository(_runtime())
    animal = _require_animal(animal_id)

    record = dict(payload)
    record["animal_id"] = animal_id

    result = _repository_call(repository, methods, record)

    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Operational record could not be persisted",
        )

    return {
        "animal_id": animal_id,
        "animal": animal,
        "record": _as_dict(result) or record,
        "source": "authoritative_persistence",
    }


@router.post("/{animal_id}/milk-entry")
def enter_milk(
    animal_id: str,
    payload: dict,
) -> dict:
    return _persist(
        animal_id,
        payload,
        (
            "create_milk_record",
            "add_milk_record",
            "save_milk_record",
        ),
    )


@router.post("/{animal_id}/feed-entry")
def enter_feed(
    animal_id: str,
    payload: dict,
) -> dict:
    return _persist(
        animal_id,
        payload,
        (
            "create_feed_record",
            "add_feed_record",
            "save_feed_record",
        ),
    )


@router.post("/{animal_id}/health-entry")
def enter_health(
    animal_id: str,
    payload: dict,
) -> dict:
    return _persist(
        animal_id,
        payload,
        (
            "create_health_record",
            "add_health_record",
            "save_health_record",
        ),
    )


@router.post("/{animal_id}/breeding-entry")
def enter_breeding(
    animal_id: str,
    payload: dict,
) -> dict:
    return _persist(
        animal_id,
        payload,
        (
            "create_breeding_record",
            "add_breeding_record",
            "save_breeding_record",
        ),
    )
