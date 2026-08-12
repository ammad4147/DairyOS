"""Standard dairy-farm KPI projections from persisted operational records.

The KPI engine deliberately calculates only metrics that can be supported by
persisted DairyOS records. Missing inputs produce ``None`` for derived values
rather than fabricated zeroes or benchmark assumptions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory


router = APIRouter(
    prefix="/farm/kpis",
    tags=["Standard Dairy KPIs"],
)


def _fresh_factory(container):
    factory = getattr(container, "repository_factory", None)
    if factory is not None:
        return factory, False
    return RepositoryFactory.create(), True


def _as_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    return None


def _record_date(record, *names):
    for name in names:
        value = getattr(record, name, None)
        converted = _as_datetime(value)
        if converted is not None:
            return converted
    return None


def _in_period(record, start, end, *date_fields):
    timestamp = _record_date(record, *date_fields)
    return timestamp is not None and start <= timestamp < end


def _conception_rate(inseminations, pregnancy_checks):
    """Match pregnancy checks to the latest prior insemination per animal."""
    ordered_inseminations = sorted(
        inseminations,
        key=lambda record: _record_date(record, "timestamp") or datetime.min.replace(tzinfo=timezone.utc),
    )
    ordered_checks = sorted(
        pregnancy_checks,
        key=lambda record: _record_date(record, "timestamp") or datetime.max.replace(tzinfo=timezone.utc),
    )

    outcomes = {}
    for check in ordered_checks:
        check_time = _record_date(check, "timestamp")
        candidates = [
            record
            for record in ordered_inseminations
            if record.animal_id == check.animal_id
            and (
                check_time is None
                or _record_date(record, "timestamp") is None
                or _record_date(record, "timestamp") <= check_time
            )
        ]
        if not candidates:
            continue
        matched = candidates[-1]
        outcomes[getattr(matched, "record_id", id(matched))] = str(
            getattr(check, "result", "")
        ).lower() in {"pregnant", "confirmed", "positive", "yes"}

    if not outcomes:
        return None
    return round((sum(outcomes.values()) / len(outcomes)) * 100, 2)


def _overview(factory, start, end):
    animals = [a for a in factory.animal().get_all() if getattr(a, "active", True)]
    milk = [
        r for r in factory.milk().get_all()
        if _in_period(r, start, end, "production_date")
    ]
    feed = [
        r for r in factory.feed().get_all()
        if _in_period(r, start, end, "feeding_date")
    ]
    health = [
        r for r in factory.health().get_all()
        if _in_period(r, start, end, "timestamp", "observation_date", "created_at")
    ]
    breeding = [
        r for r in factory.breeding().get_all()
        if _in_period(r, start, end, "timestamp")
    ]

    inseminations = [
        r for r in breeding
        if str(getattr(r, "event_type", "")).lower() in {"insemination", "service"}
    ]
    pregnancy_checks = [
        r for r in breeding
        if str(getattr(r, "event_type", "")).lower()
        in {"pregnancy_check", "pregnancy-check", "pregnancy"}
    ]
    confirmed_pregnancies = [
        r for r in pregnancy_checks
        if str(getattr(r, "result", "")).lower()
        in {"pregnant", "confirmed", "positive", "yes"}
    ]

    milk_total = sum(float(getattr(r, "total_yield", 0.0) or 0.0) for r in milk)
    production_by_animal_day = defaultdict(float)
    for record in milk:
        timestamp = _record_date(record, "production_date")
        if timestamp is not None:
            production_by_animal_day[(record.animal_id, timestamp.date())] += float(
                getattr(record, "total_yield", 0.0) or 0.0
            )

    feed_total = sum(float(getattr(r, "quantity_kg", 0.0) or 0.0) for r in feed)
    active_milking = [
        a for a in animals
        if bool(getattr(a, "is_currently_milking", False))
    ]
    youngstock = [
        a for a in animals
        if str(getattr(a, "lifecycle_status", "")).upper() in {"CALF", "HEIFER"}
    ]

    average_milk_per_animal_day = (
        milk_total / len(production_by_animal_day)
        if production_by_animal_day
        else None
    )
    feed_per_liter = feed_total / milk_total if milk_total > 0 else None
    health_per_100_animals = (
        (len(health) / len(animals)) * 100
        if animals
        else None
    )

    record_counts = {
        "animals": len(animals),
        "milk": len(milk),
        "feed": len(feed),
        "health": len(health),
        "breeding": len(breeding),
    }
    any_operational_data = any(
        record_counts[key] > 0 for key in ("milk", "feed", "health", "breeding")
    )

    return {
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "days": (end - start).days,
        },
        "data_status": "LIVE_PERSISTED_DATA" if any_operational_data else "NO_DATA",
        "record_counts": record_counts,
        "kpis": {
            "herd_size": len(animals),
            "milking_cows": len(active_milking),
            "youngstock": len(youngstock),
            "milk_production_liters": round(milk_total, 3) if milk else None,
            "average_milk_liters_per_animal_day": (
                round(average_milk_per_animal_day, 3)
                if average_milk_per_animal_day is not None else None
            ),
            "feed_consumption_kg": round(feed_total, 3) if feed else None,
            "feed_kg_per_liter_milk": (
                round(feed_per_liter, 4) if feed_per_liter is not None else None
            ),
            "health_observations": len(health) if health else None,
            "health_observations_per_100_active_animals": (
                round(health_per_100_animals, 2)
                if health_per_100_animals is not None else None
            ),
            "inseminations": len(inseminations) if inseminations else None,
            "pregnancy_checks": len(pregnancy_checks) if pregnancy_checks else None,
            "confirmed_pregnancies": len(confirmed_pregnancies) if confirmed_pregnancies else None,
            "conception_rate_percent": _conception_rate(inseminations, pregnancy_checks),
        },
        "methodology": {
            "source": "persisted operational repositories",
            "synthetic_values": False,
            "milk_basis": "persisted individual milk-production records",
            "feed_basis": "persisted feed records",
            "health_basis": "persisted health-observation records",
            "reproduction_basis": "persisted breeding records with documented pregnancy outcomes",
            "derived_values": "calculated only when required persisted inputs exist",
        },
    }


@router.get("/overview")
@router.get("")
def standard_dairy_kpi_overview(
    days: int = Query(default=30, ge=1, le=3650),
    container=Depends(get_container),
):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    factory, owns_factory = _fresh_factory(container)
    try:
        return _overview(factory, start, end)
    finally:
        if owns_factory:
            factory.close()


@router.get("/period")
def standard_dairy_kpi_period(
    start_date: date,
    end_date: date,
    container=Depends(get_container),
):
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    start = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    factory, owns_factory = _fresh_factory(container)
    try:
        return _overview(factory, start, end)
    finally:
        if owns_factory:
            factory.close()
