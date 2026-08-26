"""Persistent reproduction-management projections and operational KPIs."""

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    is_calving as _is_calving,
    is_confirmed_pregnancy as _is_confirmed_pregnancy,
    is_heat_detection as _is_heat_detection,
    is_insemination as _is_insemination,
    is_pregnancy_check as _is_pregnancy_check,
    normalize_event_type,
)
from dairyos.herd.reproduction.services.reproduction_kpi_service import ReproductionKpiService

router = APIRouter(prefix="/farm/reproduction", tags=["Reproduction Management"])


def _as_utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _fresh_factory(container):
    factory = getattr(container, "repository_factory", None)
    if factory is not None:
        factory.session.expire_all()
        return factory, False
    return RepositoryFactory.create(), True


def _serialize(record):
    return {
        "record_id": record.record_id,
        "animal_id": record.animal_id,
        "event_type": record.event_type,
        "result": record.result,
        "technician": record.technician,
        "timestamp": record.timestamp.isoformat() if record.timestamp else None,
    }


def _event_type(record) -> str:
    return normalize_event_type(getattr(record, "event_type", None))


def _conception_outcomes(inseminations, pregnancy_checks):
    """Compatibility wrapper around the authoritative KPI service."""
    return ReproductionKpiService.conception_outcomes(inseminations, pregnancy_checks)


def _conception_rate(inseminations, pregnancy_checks):
    """Calculate observed conception rate using the canonical service mapping."""
    return ReproductionKpiService.calculate_observed_conception_rate(
        inseminations,
        pregnancy_checks,
    )


def _confirmed_pregnancy_count(recent, inseminations):
    """Count unique observed pregnancy confirmations via the KPI authority."""
    pregnancy_checks = [r for r in recent if _is_pregnancy_check(r)]
    confirmation_events = [
        r for r in recent
        if _is_confirmed_pregnancy(r) and not _is_pregnancy_check(r)
    ]
    return ReproductionKpiService.confirmed_pregnancy_count(
        inseminations,
        pregnancy_checks,
        confirmation_events,
    )


def _management(records):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=365)

    recent = [
        r
        for r in records
        if r.timestamp is not None and _as_utc(r.timestamp) >= cutoff and _as_utc(r.timestamp) <= now
    ]

    event_counts = Counter(_event_type(r) for r in recent)
    inseminations = [r for r in recent if _is_insemination(r)]
    pregnancy_checks = [r for r in recent if _is_pregnancy_check(r)]
    calvings = [r for r in recent if _is_calving(r)]
    heat_events = [r for r in recent if _is_heat_detection(r)]

    outcomes = _conception_outcomes(inseminations, pregnancy_checks)
    confirmed = _confirmed_pregnancy_count(recent, inseminations)

    return {
        "period": {
            "start": cutoff.isoformat(),
            "end": now.isoformat(),
            "days": 365,
        },
        "record_count": len(recent),
        "event_counts": dict(sorted(event_counts.items())),
        "animals_with_reproductive_records": len({r.animal_id for r in recent}),
        "inseminations": len(inseminations),
        "pregnancy_checks": len(pregnancy_checks),
        "services_with_documented_outcome": len(outcomes),
        "confirmed_pregnancies": confirmed,
        "calvings": len(calvings),
        "heat_detections": len(heat_events),
        "conception_rate_percent": _conception_rate(inseminations, pregnancy_checks),
        "data_status": "NO_DATA" if not recent else "LIVE_PERSISTED_DATA",
        "records": [_serialize(r) for r in recent],
    }


@router.get("/overview")
def reproduction_overview(container=Depends(get_container)):
    factory, owns_factory = _fresh_factory(container)
    try:
        records = factory.breeding().get_all()
        return _management(records)
    finally:
        if owns_factory:
            factory.close()


@router.get("/animals/{animal_id}")
def animal_reproduction_history(animal_id: str, container=Depends(get_container)):
    factory, owns_factory = _fresh_factory(container)
    try:
        if not factory.animal().exists(animal_id):
            raise HTTPException(
                status_code=404,
                detail="Unknown Animal ID. Select an existing system-generated permanent Animal ID.",
            )
        records = [r for r in factory.breeding().get_all() if r.animal_id == animal_id]
        ordered = sorted(records, key=lambda r: _as_utc(r.timestamp))
        return {
            "animal_id": animal_id,
            "record_count": len(ordered),
            "latest_event": _serialize(ordered[-1]) if ordered else None,
            "records": [_serialize(r) for r in ordered],
            "data_status": "NO_DATA" if not ordered else "LIVE_PERSISTED_DATA",
        }
    finally:
        if owns_factory:
            factory.close()
