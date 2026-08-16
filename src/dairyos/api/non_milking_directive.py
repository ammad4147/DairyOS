from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.findings.services.operational_finding_service import (
    OperationalFindingService,
)
from dairyos.farm.production.models.non_milking_directive import (
    NonMilkingDirective,
)
from dairyos.farm.production.services.non_milking_directive_service import (
    NonMilkingDirectiveService,
)


router = APIRouter(
    prefix="/farm/animals",
    tags=["Veterinary Non-Milking Directive"],
)


class NonMilkingDirectiveRequest(BaseModel):
    directive: NonMilkingDirective
    reason: str | None = None
    changed_by: str | None = None
    effective_until: datetime | None = None


class NonMilkingClearRequest(BaseModel):
    reason: str | None = None
    changed_by: str | None = None


def _service(container):
    rf = RepositoryFactory.create(
        session=container.repository_factory.session
    )

    return (
        NonMilkingDirectiveService(
            container.animal_repository,
            finding_service=OperationalFindingService(
                rf.operational_findings()
            ),
        ),
        rf,
    )


def _serialize(animal):
    return {
        "animal_id": animal.animal_id,
        "lifecycle_status": animal.lifecycle_status,
        "is_currently_milking": animal.is_currently_milking,
        "non_milking_directive": getattr(
            animal,
            "non_milking_directive",
            NonMilkingDirective.NONE.value,
        ),
        "non_milking_since": (
            animal.non_milking_since.isoformat()
            if getattr(
                animal,
                "non_milking_since",
                None,
            )
            else None
        ),
        "non_milking_until": (
            animal.non_milking_until.isoformat()
            if getattr(
                animal,
                "non_milking_until",
                None,
            )
            else None
        ),
        "non_milking_reason": getattr(
            animal,
            "non_milking_reason",
            None,
        ),
        "non_milking_changed_by": getattr(
            animal,
            "non_milking_changed_by",
            None,
        ),
    }


@router.get("/{animal_id}/non-milking-directive")
def get_non_milking_directive(
    animal_id: str,
    container=Depends(get_container),
):
    animal = container.animal_repository.get_by_animal_id(
        animal_id
    )

    if animal is None:
        raise HTTPException(
            status_code=404,
            detail="Animal not found",
        )

    return _serialize(animal)


@router.post("/{animal_id}/non-milking-directive")
def apply_non_milking_directive(
    animal_id: str,
    payload: NonMilkingDirectiveRequest,
    container=Depends(get_container),
):
    service, rf = _service(container)

    try:
        if payload.directive is NonMilkingDirective.NONE:
            animal = service.clear(
                animal_id,
                changed_by=payload.changed_by or "Veterinarian",
                reason=payload.reason,
            )
        else:
            animal = service.apply(
                animal_id,
                payload.directive,
                reason=payload.reason,
                changed_by=payload.changed_by or "Veterinarian",
                effective_until=payload.effective_until,
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    finally:
        rf.close()

    return _serialize(animal)


@router.post("/{animal_id}/non-milking-directive/clear")
def clear_non_milking_directive(
    animal_id: str,
    payload: NonMilkingClearRequest,
    container=Depends(get_container),
):
    service, rf = _service(container)

    try:
        animal = service.clear(
            animal_id,
            changed_by=payload.changed_by or "Veterinarian",
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    finally:
        rf.close()

    return _serialize(animal)
