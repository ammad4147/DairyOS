"""Animal Passport API surface."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.application.database_aware_animal_passport import (
    DatabaseAwareLifetimeAnimalPassportService,
)
from dairyos.farm.reproduction.services.reproductive_state_service import (
    DEFAULT_REPRODUCTIVE_POLICY,
    ReproductiveStateError,
    ReproductiveStateService,
)
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService

router = APIRouter(
    prefix="/farm/animals",
    tags=["Animal Passport"],
)


def _farm_operational_date(factory) -> date:
    try:
        app_settings = getattr(factory, "app_settings", None)
        if callable(app_settings):
            return FarmSettingsService(
                app_settings()
            ).get_operational_date()
    except (AttributeError, ImportError, TypeError, ValueError):
        pass
    return datetime.now().astimezone().date()


@router.get("/{animal_id}/passport")
def get_lifetime_passport(
    animal_id: str,
    as_of_date: date | None = None,
    container=Depends(get_container),
):
    """Return the authoritative date-aware Animal Passport read model."""
    factory = container.repository_factory
    operational_date = _farm_operational_date(factory)
    passport = DatabaseAwareLifetimeAnimalPassportService(factory).build(
        animal_id,
        as_of_date=as_of_date or operational_date,
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
    operational_date = _farm_operational_date(factory)
    try:
        records = factory.breeding().get_all()
        target_events = [
            record
            for record in records
            if str(getattr(record, "animal_id", "")) == animal_id
        ]

        policy = DEFAULT_REPRODUCTIVE_POLICY
        resolved = ReproductiveStateService(policy).resolve(
            animal_id,
            target_events,
            as_of_date=as_of_date or operational_date,
            allow_unlinked_confirmation=True,
        )

        payload = asdict(resolved)
        payload["state"] = resolved.reproductive_status
        return payload
    except ReproductiveStateError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
