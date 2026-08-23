"""Operational lifecycle services for reproduction and nutrition planning."""
from __future__ import annotations

from datetime import date, datetime, timezone

from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.core.time_utils import utcnow
from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.reproduction.services.reproductive_state_service import (
    ReproductivePolicy,
    ReproductiveStateService,
)

router = APIRouter(prefix="/farm", tags=["farm-planning"])


class RationPlan(BaseModel):
    plan_id: str
    name: str
    target_group: str
    ingredients: list[dict[str, float | str]] = Field(min_length=1)
    dry_matter_kg: float | None = None
    crude_protein_pct: float | None = None
    ndf_pct: float | None = None
    energy_mcal: float | None = None
    active: bool = True
    farm_id: str = "DEFAULT"


REPRODUCTIVE_POLICY = ReproductivePolicy(
    voluntary_waiting_period_days=60,
    gestation_days=283,
    dry_off_days_before_calving=60,
)


def _breeding_record_to_event(record, operational_date: date) -> dict:
    timestamp = getattr(record, "timestamp", None)
    return {
        "animal_id": record.animal_id,
        "event_type": record.event_type,
        "event_date": timestamp.date() if timestamp is not None else operational_date,
        "result": record.result,
        "technician": record.technician,
        "record_id": record.record_id,
    }


def _serialize_historical_record(record) -> dict:
    return {
        "record_id": record.record_id,
        "event_type": record.event_type,
        "result": record.result,
        "timestamp": record.timestamp,
        "technician": record.technician,
    }


_REPRODUCTIVE_POLICY = ReproductivePolicy(
    voluntary_waiting_period_days=60,
    gestation_days=283,
    dry_off_days_before_calving=60,
)


def _breeding_record_to_resolver_event(record):
    """Adapt persisted BreedingRecord facts into resolver facts.

    BreedingRecord remains historical persistence authority. This adapter
    does not mutate or reinterpret persisted records.
    """
    raw_type = str(getattr(record, "event_type", "") or "").strip().lower()
    result = str(getattr(record, "result", "") or "").strip().lower()
    timestamp = getattr(record, "timestamp", None)

    if timestamp is None:
        return None

    negative_results = {
        "negative",
        "no",
        "open",
        "not_pregnant",
        "not pregnant",
    }

    if raw_type in {
        "insemination",
        "service",
        "ai",
        "artificial_insemination",
    }:
        event_type = "INSEMINATION"

    elif raw_type in {
        "pregnancy_negative",
    }:
        event_type = "PREGNANCY_NEGATIVE"

    elif raw_type in {
        "pregnancy_check",
        "pregnancy_diagnosis",
        "pregnancy",
    }:
        event_type = (
            "PREGNANCY_LOST"
            if result in negative_results
            else "PREGNANCY_CONFIRMED"
        )

    elif raw_type == "pregnancy_confirmed":
        event_type = "PREGNANCY_CONFIRMED"

    elif raw_type in {
        "heat_detected",
        "heat_detection",
        "heat",
        "oestrus",
        "estrus",
    }:
        event_type = "HEAT_DETECTED"

    elif raw_type in {
        "calving",
        "calved",
        "parturition",
    }:
        event_type = "CALVING"

    elif raw_type == "dry_off":
        event_type = "DRY_OFF"

    else:
        return None

    return {
        "animal_id": record.animal_id,
        "event_type": event_type,
        "event_date": timestamp,
        "result": result or None,
        "source_record_id": getattr(record, "record_id", None),
    }


def _resolve_current_reproductive_state(animal_id, records):
    """Resolve current reproductive state from persisted historical facts.

    The resolver remains the sole authority for current state.
    The persisted BreedingRecord collection remains the sole historical
    fact authority.
    """
    from datetime import timedelta

    ordered = sorted(
        records,
        key=lambda record: (
            getattr(record, "timestamp", None)
            or datetime.min.replace(tzinfo=timezone.utc)
        ),
    )

    events = []

    for record in ordered:
        event = _breeding_record_to_resolver_event(record)
        if event is not None:
            events.append(event)

    as_of_date = OperationalDateAuthority().current_date()

    effective = [
        event
        for event in events
        if event["event_date"].date() <= as_of_date
    ]

    for event in list(effective):
        if event["event_type"] != "PREGNANCY_CONFIRMED":
            continue

        prior_insemination_exists = any(
            candidate["event_type"] == "INSEMINATION"
            and candidate["event_date"] <= event["event_date"]
            for candidate in effective
        )

        if not prior_insemination_exists:
            effective.insert(
                0,
                {
                    "animal_id": animal_id,
                    "event_type": "INSEMINATION",
                    "event_date": event["event_date"] - timedelta(seconds=1),
                    "result": "IMPLICIT_CHRONOLOGY_ANCHOR",
                    "source_record_id": None,
                    "derived": True,
                },
            )

    resolver = ReproductiveStateService(_REPRODUCTIVE_POLICY)

    return resolver.resolve(
        animal_id,
        effective,
        as_of_date=as_of_date,
    )


def _current_state_api_value(state):
    """Expose the established API vocabulary from the canonical resolver."""
    if (
        getattr(state, "last_calving_date", None) is not None
        and state.last_calving_date == state.as_of_date
    ):
        return "CALVED"

    if state.pregnancy_status == "PREGNANT":
        return "PREGNANT"

    if state.reproductive_status == "HEAT_DETECTED":
        return "HEAT_OBSERVED"

    if state.reproductive_status == "BRED":
        return "INSEMINATED"

    if state.reproductive_status == "LACTATING":
        return "LACTATING"

    return "OPEN"


@router.get("/animals/{animal_id}/reproduction")
def reproductive_status(animal_id: str):
    factory = RepositoryFactory.create()

    try:
        animal = factory.animal().get_by_animal_id(animal_id)

        if animal is None:
            raise HTTPException(status_code=404, detail="Animal not found")

        records = [
            record
            for record in factory.breeding().get_all()
            if record.animal_id == animal_id
        ]

        records.sort(
            key=lambda record: (
                getattr(record, "timestamp", None)
                or datetime.min.replace(tzinfo=timezone.utc)
            )
        )

        state = _resolve_current_reproductive_state(animal_id, records)

        return {
            "animal_id": animal_id,
            "data_status": "LIVE_PERSISTED",
            "state": _current_state_api_value(state),
            "reproductive_status": state.reproductive_status,
            "pregnancy_status": state.pregnancy_status,
            "last_heat": state.last_heat_date.isoformat() if state.last_heat_date else None,
            "last_insemination": state.last_insemination_date.isoformat() if state.last_insemination_date else None,
            "pregnancy_confirmed_date": state.pregnancy_confirmed_date.isoformat() if state.pregnancy_confirmed_date else None,
            "pregnancy_result": "pregnant" if state.pregnancy_status == "PREGNANT" else None,
            "expected_calving": state.expected_calving_date.isoformat() if state.expected_calving_date else None,
            "last_calving": state.last_calving_date.isoformat() if state.last_calving_date else None,
            "lactation_number": state.lactation_number,
            "days_in_milk": state.days_in_milk,
            "eligible_to_breed": state.eligible_to_breed,
            "days_open": state.days_open,
            "expected_dry_off_date": state.expected_dry_off_date.isoformat() if state.expected_dry_off_date else None,
            "dry_period_status": state.dry_period_status,
            "events": [
                {
                    "record_id": record.record_id,
                    "event_type": record.event_type,
                    "result": record.result,
                    "technician": record.technician,
                    "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                }
                for record in records
            ],
        }

    finally:
        factory.close()


@router.get("/nutrition/rations")
def list_rations(farm_id: str = "DEFAULT"):
    factory = RepositoryFactory.create()
    try:
        model = factory.session.query(OperationalStateModel).filter(OperationalStateModel.farm_id == farm_id).first()
        plans = [] if model is None else (model.state_payload or {}).get("ration_plans", [])
        return {"data_status": "LIVE_PERSISTED" if plans else "NO_RATION_PLANS", "plans": plans}
    finally:
        factory.close()


@router.post("/nutrition/rations")
def save_ration(plan: RationPlan):
    factory = RepositoryFactory.create()
    try:
        model = factory.session.query(OperationalStateModel).filter(OperationalStateModel.farm_id == plan.farm_id).first()
        if model is None:
            model = OperationalStateModel(farm_id=plan.farm_id, operational_date=utcnow().date(), state_payload={}, created_at=utcnow())
            factory.session.add(model)
        payload = dict(model.state_payload or {})
        plans = [p for p in payload.get("ration_plans", []) if p.get("plan_id") != plan.plan_id]
        plans.append(plan.model_dump())
        payload["ration_plans"] = plans
        model.state_payload = payload
        factory.session.commit()
        return {"data_status": "PERSISTED", "plan": plan.model_dump()}
    finally:
        factory.close()
