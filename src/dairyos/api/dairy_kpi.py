"""Standard dairy-farm KPI projections from persisted operational records.

The KPI engine calculates only metrics supported by persisted DairyOS records.
Missing inputs remain ``None`` and are explicitly reported as uncovered rather
than being replaced by benchmark or zero assumptions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from dairyos.api.dependencies import get_container
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.finance.profitability.services.cost_of_production_service import CostOfProductionService

router = APIRouter(prefix="/farm/kpis", tags=["Standard Dairy KPIs"])


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
        converted = _as_datetime(getattr(record, name, None))
        if converted is not None:
            return converted
    return None


def _in_period(record, start, end, *date_fields):
    timestamp = _record_date(record, *date_fields)
    return timestamp is not None and start <= timestamp < end


def _conception_rate(inseminations, pregnancy_checks):
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
            record for record in ordered_inseminations
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


def _interval_metrics(breeding):
    """Derive reproductive intervals only where event chronology is explicit."""
    by_animal = defaultdict(list)
    for record in breeding:
        timestamp = _record_date(record, "timestamp")
        if timestamp is not None:
            by_animal[record.animal_id].append((timestamp, str(record.event_type).lower()))

    calving_intervals = []
    days_open = []
    for events in by_animal.values():
        events.sort()
        calvings = [t for t, kind in events if kind == "calving"]
        services = [t for t, kind in events if kind in {"insemination", "service"}]
        for previous, current in zip(calvings, calvings[1:]):
            calving_intervals.append((current - previous).days)
        for calving in calvings:
            prior_services = [t for t in services if t < calving]
            if prior_services:
                days_open.append((calving - prior_services[-1]).days)

    return {
        "calving_interval_days": (
            round(sum(calving_intervals) / len(calving_intervals), 2)
            if calving_intervals else None
        ),
        "days_open": round(sum(days_open) / len(days_open), 2) if days_open else None,
        "calving_interval_observations": len(calving_intervals),
        "days_open_observations": len(days_open),
    }


def _overview(factory, start, end):
    animals = [a for a in factory.animal().get_all() if getattr(a, "active", True)]
    milk = [r for r in factory.milk().get_all() if _in_period(r, start, end, "production_date")]
    feed = [r for r in factory.feed().get_all() if _in_period(r, start, end, "feeding_date")]
    health = [
        r for r in factory.health().get_all()
        if _in_period(r, start, end, "observed_at", "timestamp", "observation_date", "created_at")
    ]
    breeding = [r for r in factory.breeding().get_all() if _in_period(r, start, end, "timestamp")]
    treatments = [r for r in factory.treatment().get_all() if _in_period(r, start, end, "treated_at")]
    finance = [r for r in factory.finance().get_all() if _in_period(r, start, end, "transaction_date")]

    inseminations = [
        r for r in breeding
        if str(getattr(r, "event_type", "")).lower() in {"insemination", "service"}
    ]
    pregnancy_checks = [
        r for r in breeding
        if str(getattr(r, "event_type", "")).lower() in {"pregnancy_check", "pregnancy-check", "pregnancy"}
    ]
    confirmed_pregnancies = [
        r for r in pregnancy_checks
        if str(getattr(r, "result", "")).lower() in {"pregnant", "confirmed", "positive", "yes"}
    ]

    milk_total = sum(float(getattr(r, "total_yield", 0.0) or 0.0) for r in milk)
    production_by_animal_day = defaultdict(float)
    for record in milk:
        timestamp = _record_date(record, "production_date")
        if timestamp is not None:
            production_by_animal_day[(record.animal_id, timestamp.date())] += float(getattr(record, "total_yield", 0.0) or 0.0)

    daily_totals = defaultdict(float)
    for (_, production_day), litres in production_by_animal_day.items():
        daily_totals[production_day] += litres

    feed_total = sum(float(getattr(r, "quantity_kg", 0.0) or 0.0) for r in feed)
    active_milking = [a for a in animals if bool(getattr(a, "is_currently_milking", False))]
    youngstock = [
        a for a in animals
        if str(getattr(a, "lifecycle_status", "")).upper() in {"CALF", "HEIFER"}
    ]

    average_milk_per_animal_day = milk_total / len(production_by_animal_day) if production_by_animal_day else None
    feed_per_liter = feed_total / milk_total if milk_total > 0 else None
    health_per_100_animals = (len(health) / len(animals)) * 100 if animals else None
    treatment_rate = (len({r.animal_id for r in treatments}) / len(animals)) * 100 if animals else None

    cost = CostOfProductionService().evaluate(milk, finance, days=(end - start).days, now=end)
    expense_categories = cost.get("expense_by_category", {})

    interval_metrics = _interval_metrics(breeding)
    covered = {
        "milk_per_cow_day": average_milk_per_animal_day is not None,
        "herd_average": average_milk_per_animal_day is not None,
        "peak_daily_milk": bool(daily_totals),
        "conception_rate": _conception_rate(inseminations, pregnancy_checks) is not None,
        "calving_interval": interval_metrics["calving_interval_days"] is not None,
        "days_open": interval_metrics["days_open"] is not None,
        "feed_conversion": feed_per_liter is not None,
        "feed_cost_per_litre": "FEED" in expense_categories and milk_total > 0,
        "cost_per_litre": cost.get("cost_per_litre") is not None,
        "labour_per_litre": "LABOUR" in expense_categories and milk_total > 0,
        "treatment_rate": treatment_rate is not None,
        "mortality_rate": False,
        "culling_rate": False,
        "persistency": False,
    }

    return {
        "period": {"start": start.isoformat(), "end": end.isoformat(), "days": (end - start).days},
        "data_status": "LIVE_PERSISTED_DATA" if any((milk, feed, health, breeding, treatments, finance)) else "NO_DATA",
        "record_counts": {
            "animals": len(animals), "milk": len(milk), "feed": len(feed),
            "health": len(health), "breeding": len(breeding),
            "treatments": len(treatments), "finance": len(finance),
        },
        "kpis": {
            "herd_size": len(animals),
            "milking_cows": len(active_milking),
            "youngstock": len(youngstock),
            "milk_production_liters": round(milk_total, 3) if milk else None,
            "average_milk_liters_per_animal_day": round(average_milk_per_animal_day, 3) if average_milk_per_animal_day is not None else None,
            "peak_daily_milk_liters": round(max(daily_totals.values()), 3) if daily_totals else None,
            "feed_consumption_kg": round(feed_total, 3) if feed else None,
            "feed_kg_per_liter_milk": round(feed_per_liter, 4) if feed_per_liter is not None else None,
            "health_observations": len(health) if health else None,
            "health_observations_per_100_active_animals": round(health_per_100_animals, 2) if health_per_100_animals is not None else None,
            "treatment_rate_percent": round(treatment_rate, 2) if treatment_rate is not None else None,
            "inseminations": len(inseminations) if inseminations else None,
            "pregnancy_checks": len(pregnancy_checks) if pregnancy_checks else None,
            "confirmed_pregnancies": len(confirmed_pregnancies) if confirmed_pregnancies else None,
            "conception_rate_percent": _conception_rate(inseminations, pregnancy_checks),
            **interval_metrics,
            "feed_cost_per_litre": round(float(expense_categories.get("FEED", 0)) / milk_total, 4) if covered["feed_cost_per_litre"] else None,
            "labour_cost_per_litre": round(float(expense_categories.get("LABOUR", 0)) / milk_total, 4) if covered["labour_per_litre"] else None,
            "cost_per_litre": cost.get("cost_per_litre"),
        },
        "coverage": {
            "complete_metrics": [name for name, value in covered.items() if value],
            "missing_metrics": [name for name, value in covered.items() if not value],
            "definitions": {
                "milk_per_cow_day": "persisted milk litres divided by animal-days with milk records",
                "peak_daily_milk": "maximum aggregate litres across persisted animal/day milk records",
                "treatment_rate": "distinct treated animals divided by active animals for the period",
                "feed_cost_per_litre": "persisted FEED expense divided by persisted non-withheld milk litres",
                "labour_per_litre": "persisted LABOUR expense divided by persisted non-withheld milk litres",
            },
        },
        "methodology": {
            "source": "persisted operational repositories",
            "synthetic_values": False,
            "derived_values": "calculated only when required persisted inputs exist",
            "unsupported_without_history": ["mortality_rate", "culling_rate", "persistency"],
        },
    }


@router.get("/overview")
@router.get("")
def standard_dairy_kpi_overview(days: int = Query(default=30, ge=1, le=3650), container=Depends(get_container)):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    factory, owns_factory = _fresh_factory(container)
    try:
        return _overview(factory, start, end)
    finally:
        if owns_factory:
            factory.close()


@router.get("/period")
def standard_dairy_kpi_period(start_date: date, end_date: date, container=Depends(get_container)):
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
