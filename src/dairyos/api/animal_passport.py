"""Lifetime Animal Passport API surface."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

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
    container=Depends(get_container),
):
    """Return the authoritative read-side lifetime Animal Passport."""
    factory = RepositoryFactory.create()

    try:
        passport = LifetimeAnimalPassportService(factory).build(
            animal_id
        )

        if passport is None:
            raise HTTPException(
                status_code=404,
                detail="Animal not found",
            )

        return passport

    finally:
        factory.close()
