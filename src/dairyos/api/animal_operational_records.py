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
        raise HTTPException(status_code=503, detail="Authoritative animal repository is not available")

    animal = _repository_call(
        repository,
        ("get_by_animal_id", "get_by_id", "find_by_animal_id", "find_by_id", "find"),
        animal_id,
    )
    if animal is None:
        raise HTTPException(status_code=404, detail=f"Animal not found: {animal_id}")
    return _as_dict(animal)


def _repository_records(factory, repository_name: str, animal_id: str, method_names: tuple[str, ...]):
    repository = getattr(factory, repository_name)()
    records = _repository_call(repository, method_names, animal_id)
    if records is None:
        return []
    if isinstance(records, (list, tuple)):
        return list(records)
    return [records]


def _record_payload(animal_id: str, animal: dict, records: list) -> dict:
    return {
        "animal_id": animal_id,
        "animal": animal,
        "records": [_as_dict(record) for record in records],
        "count": len(records),
        "source": "authoritative_persistence",
    }


def _factory():
    runtime = _runtime()
    if runtime is None or getattr(runtime, "repository_factory", None) is None:
        raise HTTPException(status_code=503, detail="Canonical repository factory is not available")
    return runtime.repository_factory


@router.get("/{animal_id}/milk")
def animal_milk_records(animal_id: str) -> dict:
    animal = _require_animal(animal_id)
    records = _repository_records(
        _factory(),
        "milk",
        animal_id,
        ("get_by_animal_id",),
    )
    return _record_payload(animal_id, animal, records)


@router.get("/{animal_id}/feed")
def animal_feed_records(animal_id: str) -> dict:
    animal = _require_animal(animal_id)
    records = _repository_records(
        _factory(),
        "feed",
        animal_id,
        ("get_by_animal_id",),
    )
    return _record_payload(animal_id, animal, records)


@router.get("/{animal_id}/health")
def animal_health_records(animal_id: str) -> dict:
    animal = _require_animal(animal_id)
    records = _repository_records(
        _factory(),
        "health",
        animal_id,
        ("get_by_animal_id",),
    )
    return _record_payload(animal_id, animal, records)


@router.get("/{animal_id}/breeding")
def animal_breeding_records(animal_id: str) -> dict:
    animal = _require_animal(animal_id)
    records = _repository_records(
        _factory(),
        "breeding",
        animal_id,
        ("get_by_animal_id",),
    )
    return _record_payload(animal_id, animal, records)


@router.get("/{animal_id}/treatments")
def animal_treatment_records(animal_id: str) -> dict:
    animal = _require_animal(animal_id)
    records = _repository_records(
        _factory(),
        "treatment",
        animal_id,
        ("get_by_animal", "get_by_animal_id"),
    )
    return _record_payload(animal_id, animal, records)


@router.get("/{animal_id}/finance")
def animal_finance_records(animal_id: str) -> dict:
    animal = _require_animal(animal_id)
    records = _repository_records(
        _factory(),
        "finance",
        animal_id,
        ("get_by_animal_id",),
    )
    return _record_payload(animal_id, animal, records)


@router.get("/{animal_id}/operational-records")
def animal_operational_records(animal_id: str) -> dict:
    """Single persisted animal-centric operational record surface."""
    animal = _require_animal(animal_id)
    factory = _factory()

    return {
        "animal_id": animal_id,
        "animal": animal,
        "milk": [_as_dict(record) for record in _repository_records(factory, "milk", animal_id, ("get_by_animal_id",))],
        "feed": [_as_dict(record) for record in _repository_records(factory, "feed", animal_id, ("get_by_animal_id",))],
        "health": [_as_dict(record) for record in _repository_records(factory, "health", animal_id, ("get_by_animal_id",))],
        "breeding": [_as_dict(record) for record in _repository_records(factory, "breeding", animal_id, ("get_by_animal_id",))],
        "treatments": [_as_dict(record) for record in _repository_records(factory, "treatment", animal_id, ("get_by_animal", "get_by_animal_id"))],
        "finance": [_as_dict(record) for record in _repository_records(factory, "finance", animal_id, ("get_by_animal_id",))],
        "source": "authoritative_persistence",
    }
