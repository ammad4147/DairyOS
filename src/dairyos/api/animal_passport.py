"""Animal Passport API surface."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from dairyos.api.dependencies import get_container
from dairyos.application.animal_passport import LifetimeAnimalPassportService
from dairyos.data.repositories.repository_factory import RepositoryFactory


router = APIRouter(
    prefix="/farm/animals",
    tags=["Animal Passport"],
)


@router.get("/{animal_id}/passport")
def get_lifetime_passport(
    animal_id: str,
    as_of_date: date | None = Query(
        default=None,
        description="Optional operational date for historical passport state.",
    ),
    container=Depends(get_container),
):
    """Return the authoritative date-aware Animal Passport read model."""
    factory = RepositoryFactory.create()

    try:
        passport = LifetimeAnimalPassportService(
            factory
        ).build(
            animal_id,
            as_of_date=as_of_date,
        )

        if passport is None:
            raise HTTPException(
                status_code=404,
                detail="Animal not found",
            )

        return passport

    finally:
        factory.close()
