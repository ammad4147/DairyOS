"""Animal Passport API surface."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from dairyos.api.dependencies import get_container
from dairyos.application.animal_passport import LifetimeAnimalPassportService
from dairyos.data.repositories.repository_factory import RepositoryFactory
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


@router.get("/{animal_id}/reproduction")
def get_reproductive_state(
    animal_id: str,
    as_of_date: date | None = Query(
        default=None,
        description="Optional operational date for reproductive state resolution.",
    ),
    container=Depends(get_container),
):
    """Return the authoritative reproductive state for one registered animal.

    This read endpoint consumes persisted breeding facts. A standalone
    pregnancy-confirmed observation is accepted as direct outcome evidence;
    it does not fabricate an insemination/service record. Consequently the
    state can be PREGNANT while expected calving and days-open remain unknown
    when no service date is documented.
    """
    factory = RepositoryFactory.create()
    try:
        records = factory.breeding().get_all()
        target_events = [
            record
            for record in records
            if str(getattr(record, "animal_id", "")) == animal_id
        ]

        # These are the established reproductive-policy defaults used by the
        # operational read model. They do not create farm facts; they only
        # govern derived dates when the underlying observed facts exist.
        policy = ReproductivePolicy(
            voluntary_waiting_period_days=60,
            gestation_days=280,
            dry_off_days_before_calving=60,
        )
        service = ReproductiveStateService(policy)
        resolved = service.resolve(
            animal_id,
            target_events,
            as_of_date=as_of_date or date.today(),
            allow_unlinked_confirmation=True,
        )

        payload = asdict(resolved)
        # ``state`` is the stable API vocabulary consumed by the animal
        # reproductive-status surface. Keep the detailed domain fields intact
        # for callers that need the full read model.
        payload["state"] = resolved.reproductive_status
        return payload
    except ReproductiveStateError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        factory.close()
