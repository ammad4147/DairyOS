"""Persistent reproduction-management projections and operational KPIs."""

from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory


router = APIRouter(
    prefix="/farm/reproduction",
    tags=["Reproduction Management"],
)


def _fresh_factory(container):
    factory = getattr(container, "repository_factory", None)
    if factory is not None:
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
    """Normalize UI/API reproduction event vocabulary for KPI projections."""
    return str(getattr(record, "event_type", "")).strip().lower().replace("-", "_")


def _is_insemination(record) -> bool:
    return _event_type(record) in {"insemination", "service"}


def _is_pregnancy_check(record) -> bool:
    return _event_type(record) in {
        "pregnancy_check",
        "pregnancy_diagnosis",
        "pregnancy",
    }


def _is_confirmed_pregnancy(record) -> bool:
    event = _event_type(record)
    result = str(getattr(record, "result", "")).strip().lower()
    return event == "pregnancy_confirmed" or (
        _is_pregnancy_check(record)
        and result in {"pregnant", "confirmed", "positive", "yes"}
    )


def _is_calving(record) -> bool:
    return _event_type(record) in {"calving", "calved", "parturition"}


def _is_heat_detection(record) -> bool:
    return _event_type(record) in {"heat_detection", "heat_detected", "heat", "oestrus", "estrus"}


def _conception_rate(inseminations, pregnancy_checks):
    """Return conception rate only for inseminations with a documented outcome.

    A pregnancy check is matched to the latest insemination for the same animal
    that occurred on or before the check. Unmatched historical inseminations are
    excluded from the denominator rather than being treated as failed outcomes.
    This prevents incomplete historical records from fabricating a low rate.
    """
    ordered_inseminations = sorted(
        inseminations,
        key=lambda record: record.timestamp or datetime.min.replace(tzinfo=timezone.utc),
    )
    ordered_checks = sorted(
        pregnancy_checks,
        key=lambda record: record.timestamp or datetime.max.replace(tzinfo=timezone.utc),
    )

    outcomes = {}
    for check in ordered_checks:
        check_time = check.timestamp
        candidates = [
            record
            for record in ordered_inseminations
            if record.animal_id == check.animal_id
            and (
                check_time is None
                or record.timestamp is None
                or record.timestamp <= check_time
            )
        ]
        if not candidates:
            continue
        matched = candidates[-1]
        outcomes[matched.record_id] = _is_confirmed_pregnancy(check)

    if not outcomes:
        return None
    return round((sum(outcomes.values()) / len(outcomes)) * 100, 2)


def _management(records):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=365)
    recent = [r for r in records if r.timestamp is None or r.timestamp >= cutoff]

    event_counts = Counter(_event_type(r) for r in recent)
    inseminations = [r for r in recent if _is_insemination(r)]
    pregnancy_checks = [r for r in recent if _is_pregnancy_check(r)]
    confirmed = [r for r in recent if _is_confirmed_pregnancy(r)]
    calvings = [r for r in recent if _is_calving(r)]
    heat_events = [r for r in recent if _is_heat_detection(r)]

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
        "confirmed_pregnancies": len(confirmed),
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
        ordered = sorted(records, key=lambda r: r.timestamp or datetime.min.replace(tzinfo=timezone.utc))
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
