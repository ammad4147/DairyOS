from __future__ import annotations

from fastapi import APIRouter, HTTPException

from dairyos.api.animals import _as_dict, _repository, _repository_call, _runtime

router = APIRouter(
    prefix="/farm/animals",
    tags=["animal-operational-records"],
)


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


def _record_endpoint(
    animal_id: str,
    repository_methods: tuple[str, ...],
) -> dict:
    repository = _repository(_runtime())

    animal = _require_animal(animal_id)

    records = _repository_call(
        repository,
        repository_methods,
        animal_id,
    )

    if records is None:
        records = []

    if not isinstance(records, (list, tuple)):
        records = [records]

    return {
        "animal_id": animal_id,
        "animal": animal,
        "records": [_as_dict(record) for record in records],
        "count": len(records),
        "source": "authoritative_persistence",
    }


@router.get("/{animal_id}/milk")
def animal_milk_records(animal_id: str) -> dict:
    return _record_endpoint(
        animal_id,
        (
            "list_milk_for_animal",
            "get_milk_for_animal",
            "milk_for_animal",
        ),
    )


@router.get("/{animal_id}/feed")
def animal_feed_records(animal_id: str) -> dict:
    return _record_endpoint(
        animal_id,
        (
            "list_feed_for_animal",
            "get_feed_for_animal",
            "feed_for_animal",
        ),
    )


@router.get("/{animal_id}/health")
def animal_health_records(animal_id: str) -> dict:
    return _record_endpoint(
        animal_id,
        (
            "list_health_for_animal",
            "get_health_for_animal",
            "health_for_animal",
        ),
    )


@router.get("/{animal_id}/breeding")
def animal_breeding_records(animal_id: str) -> dict:
    return _record_endpoint(
        animal_id,
        (
            "list_breeding_for_animal",
            "get_breeding_for_animal",
            "breeding_for_animal",
        ),
    )


@router.get("/{animal_id}/operational-records")
def animal_operational_records(animal_id: str) -> dict:
    """
    Single animal-centric operational record surface.

    This endpoint deliberately returns only persisted records.
    Missing operational history is represented by an empty collection,
    never by fabricated values.
    """
    animal = _require_animal(animal_id)

    return {
        "animal_id": animal_id,
        "animal": animal,
        "milk": animal_milk_records(animal_id)["records"],
        "feed": animal_feed_records(animal_id)["records"],
        "health": animal_health_records(animal_id)["records"],
        "breeding": animal_breeding_records(animal_id)["records"],
        "source": "authoritative_persistence",
    }
