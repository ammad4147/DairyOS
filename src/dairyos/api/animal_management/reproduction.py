from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.reproduction.services.reproductive_state_service import (
    ReproductivePolicy,
    ReproductiveStateService,
)

from .router import router


_POLICY = ReproductivePolicy(
    voluntary_waiting_period_days=50,
    gestation_days=283,
    dry_off_days_before_calving=60,
)


def _as_of_date(factory) -> object:
    """Use the farm operational date when available, with a UTC fallback."""
    try:
        from dairyos.farm.settings.services.farm_settings_service import (
            FarmSettingsService,
        )

        return FarmSettingsService(factory.app_settings()).get_operational_date()
    except (AttributeError, ImportError, TypeError, ValueError):
        return datetime.now(timezone.utc).date()


@router.get("/animals/{animal_id}/reproduction")
def animal_reproduction_status(
    animal_id: str,
    container=Depends(get_container),
):
    """Return the authoritative reproductive state for one animal.

    The response is derived only from persisted breeding records. A bare
    pregnancy confirmation is allowed here because the operational UI can
    receive a documented confirmation without the service record being
    available in the same projection; the state service remains the single
    authority for all resulting status fields.
    """
    factory = getattr(container, "repository_factory", None)
    owns_factory = False
    if factory is None:
        factory = RepositoryFactory.create()
        owns_factory = True

    try:
        if not factory.animal().exists(animal_id):
            raise HTTPException(status_code=404, detail="Animal not found")

        records = [
            record
            for record in factory.breeding().get_all()
            if record.animal_id == animal_id
        ]
        state = ReproductiveStateService(_POLICY).resolve(
            animal_id,
            records,
            as_of_date=_as_of_date(factory),
            allow_unlinked_confirmation=True,
        )

        return {
            "animal_id": state.animal_id,
            "state": state.reproductive_status,
            "reproductive_status": state.reproductive_status,
            "pregnancy_status": state.pregnancy_status,
            "last_calving": (
                state.last_calving_date.isoformat()
                if state.last_calving_date
                else None
            ),
            "lactation_number": state.lactation_number,
            "days_in_milk": state.days_in_milk,
            "voluntary_waiting_period_end": (
                state.voluntary_waiting_period_end.isoformat()
                if state.voluntary_waiting_period_end
                else None
            ),
            "eligible_to_breed": state.eligible_to_breed,
            "last_insemination": (
                state.last_insemination_date.isoformat()
                if state.last_insemination_date
                else None
            ),
            "pregnancy_confirmed": (
                state.pregnancy_confirmed_date.isoformat()
                if state.pregnancy_confirmed_date
                else None
            ),
            "expected_calving": (
                state.expected_calving_date.isoformat()
                if state.expected_calving_date
                else None
            ),
            "days_open": state.days_open,
            "expected_dry_off": (
                state.expected_dry_off_date.isoformat()
                if state.expected_dry_off_date
                else None
            ),
            "dry_period_status": state.dry_period_status,
            "as_of_date": state.as_of_date.isoformat(),
            "data_status": "NO_DATA" if not records else "LIVE_PERSISTED_DATA",
        }
    finally:
        if owns_factory:
            factory.close()
