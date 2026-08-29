"""Animal Passport API surface."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.application.database_aware_animal_passport import (
    DatabaseAwareLifetimeAnimalPassportService,
)
from dairyos.farm.reproduction.services.reproductive_state_service import (
    ReproductivePolicy,
    ReproductiveStateError,
    ReproductiveStateService,
)

router = APIRouter(
    prefix="/farm/animals",
    tags=["Animal Passport"],
)


@router.get("/{animal_id}/passport")
def get_lifetime_passport(
    animal_id: str,
    as_of_date: date | None = None,
    container=Depends(get_container),
):
    """Return the authoritative date-aware Animal Passport read model."""
    factory = container.repository_factory
    passport = DatabaseAwareLifetimeAnimalPassportService(factory).build(
        animal_id,
        as_of_date=as_of_date,
    )
    if passport is None:
        raise HTTPException(status_code=404, detail="Animal not found")
    return passport


@router.get("/{animal_id}/reproduction")
def get_reproductive_state(
    animal_id: str,
    as_of_date: date | None = None,
    container=Depends(get_container),
):
    """Return the authoritative reproductive state for one registered animal."""
    factory = container.repository_factory
    try:
        records = factory.breeding().get_all()
        target_events = [
            record
            for record in records
            if str(getattr(record, "animal_id", "")) == animal_id
        ]

        policy = ReproductivePolicy(
            voluntary_waiting_period_days=60,
            gestation_days=280,
            dry_off_days_before_calving=60,
        )
        resolved = ReproductiveStateService(policy).resolve(
            animal_id,
            target_events,
            as_of_date=as_of_date or date.today(),
            allow_unlinked_confirmation=True,
        )

        payload = asdict(resolved)
        payload["state"] = resolved.reproductive_status
        return payload
    except ReproductiveStateError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
