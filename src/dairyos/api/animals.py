from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field


router = APIRouter(
    prefix="/farm/animals",
    tags=["animals"],
)


class AnimalCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    animal_type: str = Field(
        default="COW",
        min_length=1,
    )
    ear_tag: str | None = None
    rfid: str | None = None
    breed: str | None = None
    sex: str | None = "FEMALE"
    date_of_birth: date | None = None
    dam_id: str | None = None
    sire_id: str | None = None
    lifecycle_status: str = "HEIFER"
    is_currently_milking: bool = False
    milking_frequency: str | None = None
    production_group: str | None = None
    location: str | None = None
    active: bool = True


def _runtime() -> Any:
    try:
        from dairyos.application_runtime import (
            get_application_runtime,
        )

        return get_application_runtime()
    except Exception:
        return None


def _repository(runtime: Any) -> Any:
    if runtime is None:
        return None

    for name in (
        "animal_repository",
        "animals_repository",
        "animal_operational_repository",
    ):
        repository = getattr(
            runtime,
            name,
            None,
        )

        if repository is not None:
            return repository

    factory = getattr(
        runtime,
        "repository_factory",
        None,
    )

    if factory is not None:
        for name in (
            "animal_repository",
            "animals",
            "animal",
        ):
            method = getattr(
                factory,
                name,
                None,
            )

            if callable(method):
                try:
                    repository = method()

                    if repository is not None:
                        return repository

                except Exception:
                    pass

    return None


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, dict):
        return dict(value)

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "to_dict"):
        return value.to_dict()

    if hasattr(value, "__dict__"):
        return {
            key: item
            for key, item in vars(value).items()
            if not key.startswith("_")
        }

    return {}


def _repository_call(
    repository: Any,
    names: tuple[str, ...],
    *args: Any,
    **kwargs: Any,
) -> Any:
    if repository is None:
        return None

    for name in names:
        method = getattr(
            repository,
            name,
            None,
        )

        if callable(method):
            return method(
                *args,
                **kwargs,
            )

    return None


def _generate_animal_id(
    repository: Any,
) -> str:
    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d%H%M%S")

    existing = _repository_call(
        repository,
        (
            "list",
            "list_all",
            "get_all",
        ),
    )

    if existing is None:
        return f"AN-{timestamp}"

    try:
        count = len(list(existing))
    except Exception:
        count = 0

    return (
        f"AN-{timestamp}-{count + 1:03d}"
    )


def _persist(
    repository: Any,
    payload: dict[str, Any],
) -> Any:
    if repository is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Authoritative animal repository "
                "is not available"
            ),
        )

    animal_id = payload["animal_id"]

    existing = _repository_call(
        repository,
        (
            "get_by_animal_id",
            "get_by_id",
            "find_by_id",
            "find",
        ),
        animal_id,
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Animal ID already exists: "
                f"{animal_id}"
            ),
        )

    created = _repository_call(
        repository,
        (
            "create",
            "add",
            "save",
            "insert",
        ),
        payload,
    )

    if created is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Animal could not be persisted "
                "to the authoritative repository"
            ),
        )

    return created


@router.get("")
def list_animals() -> list[dict[str, Any]]:
    runtime = _runtime()
    repository = _repository(runtime)

    if repository is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Authoritative animal repository "
                "is not available"
            ),
        )

    records = _repository_call(
        repository,
        (
            "list",
            "list_all",
            "get_all",
            "all",
        ),
    )

    if records is None:
        return []

    return [
        _as_dict(record)
        for record in records
    ]


@router.post(
    "",
    status_code=201,
)
def create_animal(
    request: AnimalCreateRequest,
) -> dict[str, Any]:
    runtime = _runtime()
    repository = _repository(runtime)

    payload = request.model_dump(
        exclude_none=True
    )

    payload["animal_id"] = (
        _generate_animal_id(repository)
    )

    payload["active"] = True

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    payload["created_at"] = timestamp
    payload["updated_at"] = timestamp

    created = _persist(
        repository,
        payload,
    )

    result = _as_dict(created)

    if not result:
        result = payload

    result.setdefault(
        "animal_id",
        payload["animal_id"],
    )

    result.setdefault(
        "active",
        True,
    )

    return result


@router.get("/{animal_id}")
def get_animal(
    animal_id: str,
) -> dict[str, Any]:
    runtime = _runtime()
    repository = _repository(runtime)

    if repository is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Authoritative animal repository "
                "is not available"
            ),
        )

    record = _repository_call(
        repository,
        (
            "get_by_animal_id",
            "get_by_id",
            "find_by_id",
            "find",
        ),
        animal_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Animal not found: {animal_id}"
            ),
        )

    return _as_dict(record)
