"""Standard dairy-farm KPI projections from persisted operational records."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from dairyos.api.dependencies import get_container
from dairyos.farm.settings.services.operational_date_authority import OperationalDateAuthority
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.finance.profitability.services.cost_of_production_service import CostOfProductionService
from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    is_calving as _is_calving,
    is_confirmed_pregnancy as _is_confirmed_pregnancy,
    is_insemination as _is_insemination,
    is_pregnancy_check as _is_pregnancy_check,
)
from dairyos.herd.reproduction.services.reproduction_kpi_service import ReproductionKpiService

router = APIRouter(prefix="/farm/kpis", tags=["Standard Dairy KPIs"])


def _fresh_factory(container):
    factory = getattr(container, "repository_factory", None)
    if factory is not None:
        factory.session.expire_all()
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


def _has_entered_yield(record) -> bool:
    if getattr(record, "total_yield", None) is not None:
        return True
    return any(getattr(record, field, None) is not None for field in ("morning_yield", "afternoon_yield", "evening_yield"))


def _in_period(record, start, end, *date_fields):
    timestamp = _record_date(record, *date_fields)
    return timestamp is not None and start <= timestamp < end


def _conception_outcomes(inseminations, pregnancy_checks):
    return ReproductionKpiService.conception_outcomes(inseminations, pregnancy_checks)


def _conception_rate(inseminations, pregnancy_checks):
    return ReproductionKpiService.calculate_observed_conception_rate(inseminations, pregnancy_checks)


def _confirmed_pregnancy_count(breeding, inseminations, pregnancy_checks):
    confirmations = [
        record
        for record in breeding
        if _is_confirmed_pregnancy(record) and not _is_pregnancy_check(record)
    ]
    return ReproductionKpiService.confirmed_pregnancy_count(
        inseminations,
        pregnancy_checks,
        confirmations,
    )


def _interval_metrics(breeding):
    """Calculate observed calving interval and days open.

    Days open is the observed interval from the most recent calving to the
    subsequent insemination/service that established the pregnancy cycle. It
    is not calculated from gestation length and does not require a pregnancy
    diagnosis merely to establish the service date. A service before any
    observed calving is not treated as a days-open observation.
    """
    by_animal = defaultdict(list)
    for record in breeding:
        timestamp = _record_date(record, "timestamp")
        if timestamp is not None:
            by_animal[record.animal_id].append((timestamp, record))

    calving_intervals = []
    days_open = []
    for events in by_animal.values():
        events.sort(key=lambda item: item[0])
        calvings = [(t, r) for t, r in events if _is_calving(r)]

        for previous, current in zip(calvings, calvings[1:]):
            calving_intervals.append((current[0] - previous[0]).days)

        for index, (calving_time, _) in enumerate(calvings):
            next_calving_time = calvings[index + 1][0] if index + 1 < len(calvings) else None
            services = [
                t for t, record in events
                if _is_insemination(record)
                and t > calving_time
                and (next_calving_time is None or t < next_calving_time)
            ]
            if services:
                days_open.append((services[0] - calving_time).days)

    return {
        "calving_interval_days": round(sum(calving_intervals) / len(calving_intervals), 2) if calving_intervals else None,
        "days_open": round(sum(days_open) / len(days_open), 2) if days_open else None,
        "calving_interval_observations": len(calving_intervals),
        "days_open_observations": len(days_open),
    }


def _overview(factory, start, end):
    animals = [a for a in factory.animal().get_all() if getattr(a, "active", True)]
    milk = [r for r in factory.milk().get_all() if _in_period(r, start, end, "production_date")]
    feed = [r for r in factory.feed().get_all() if _in_period(r, start, end, "feeding_date")]
    health = [r for r in factory.health().get_all() if _in_period(r, start, end, "observed_at", "timestamp", "observation_date", "created_at")]
    breeding = [r for r in factory.breeding().get_all() if _in_period(r, start, end, "timestamp")]
    treatments = [r for r in factory.treatment().get_all() if _in_period(r, start, end, "treated_at")]
    finance = [r for r in factory.finance().get_all() if _in_period(r, start, end, "transaction_date")]

    inseminations = [r for r in breeding if _is_insemination(r)]
    pregnancy_checks = [r for r in breeding if _is_pregnancy_check(r)]
    conception_outcomes = _conception_outcomes(inseminations, pregnancy_checks)
    confirmed_pregnancies = _confirmed_pregnancy_count(breeding, inseminations, pregnancy_checks)

    milk_total = sum(float(getattr(r, "total_yield", 0.0) or 0.0) for r in milk)
    production_by_animal_day = defaultdict(float)
    for record in milk:
        if not _has_entered_yield(record):
            continue
        timestamp = _record_date(record, "production_date")
        if timestamp is not None:
            production_by_animal_day[(record.animal_id, timestamp.date())] += float(getattr(record, "total_yield", 0.0) or 0.0)

    daily_totals = defaultdict(float)
    for (_, production_day), litres in production_by_animal_day.items():
        daily_totals[production_day] += litres

    feed_total = sum(float(getattr(r, "quantity_kg", 0.0) or 0.0) for r in feed)
    active_milking = [a for a in animals if bool(getattr(a, "is_currently_milking", False))]
    youngstock = [a for a in animals if str(getattr(a, "lifecycle_status", "")).upper() in {"CALF", "HEIFER"}]

    average_milk_per_animal_day = milk_total / len(production_by_animal_day) if production_by_animal_day else None
    feed_per_liter = None
    health_per_100_animals = (len(health) / len(animals)) * 100 if animals else None
    treatment_rate = (len({r.animal_id for r in treatments}) / len(animals)) * 100 if animals else None

    cost = CostOfProductionService().evaluate(milk, finance, days=(end - start).days, now=end)
    expense_categories = cost.get("expense_by_category", {})

    interval_metrics = _interval_metrics(breeding)
    conception_rate = ReproductionKpiService.calculate_observed_conception_rate(inseminations, pregnancy_checks)
    covered = {
        "milk_per_cow_day": average_milk_per_animal_day is not None,
        "herd_average": average_milk_per_animal_day is not None,
        "peak_daily_milk": bool(daily_totals),
        "conception_rate": conception_rate is not None,
        "calving_interval": interval_metrics["calving_interval_days"] is not None,
        "days_open": interval_metrics["days_open"] is not None,
        "feed_conversion": False,
        "feed_cost_per_litre": "FEED" in expense_categories and milk_total > 0,
        "cost_per_litre": cost.get("cost_per_litre") is not None,
        "labour_per_litre": "LABOUR" in expense_categories and milk_total > 0,
        "treatment_rate": treatment_rate is not None,
        "mortality_rate": False,
        "culling_rate": False,
        "persistency": False,
    }

    has_kpi_anchor_data = bool(milk)

    return {
        "period": {"start": start.isoformat(), "end": end.isoformat(), "days": (end - start).days},
        "data_status": "LIVE_PERSISTED_DATA" if has_kpi_anchor_data else "NO_DATA",
        "record_counts": {"animals": len(animals), "milk": len(milk), "feed": len(feed), "health": len(health), "breeding": len(breeding), "treatments": len(treatments), "finance": len(finance)},
        "kpis": {
            "herd_size": len(animals), "milking_cows": len(active_milking), "youngstock": len(youngstock),
            "milk_production_liters": round(milk_total, 3) if milk else None,
            "average_milk_liters_per_animal_day": round(average_milk_per_animal_day, 3) if average_milk_per_animal_day is not None else None,
            "peak_daily_milk_liters": round(max(daily_totals.values()), 3) if daily_totals else None,
            "feed_consumption_kg": round(feed_total, 3) if feed else None,
            "feed_kg_per_liter_milk": feed_per_liter,
            "health_observations": len(health) if health else None,
            "health_observations_per_100_active_animals": round(health_per_100_animals, 2) if health_per_100_animals is not None else None,
            "treatment_rate_percent": round(treatment_rate, 2) if treatment_rate is not None else None,
            "inseminations": len(inseminations) if inseminations else None,
            "pregnancy_checks": len(pregnancy_checks) if pregnancy_checks else None,
            "confirmed_pregnancies": confirmed_pregnancies if confirmed_pregnancies else None,
            "conception_rate_percent": conception_rate,
            **interval_metrics,
            "feed_cost_per_litre": round(float(expense_categories.get("FEED", 0)) / milk_total, 4) if covered["feed_cost_per_litre"] else None,
            "labour_cost_per_litre": round(float(expense_categories.get("LABOUR", 0)) / milk_total, 4) if covered["labour_per_litre"] else None,
            "cost_per_litre": cost.get("cost_per_litre"),
        },
        "coverage": {
            "complete_metrics": [name for name, value in covered.items() if value],
            "missing_metrics": [name for name, value in covered.items() if not value],
            "definitions": {
                "milk_per_cow_day": "persisted milk litres divided by animal-days with actual milk observations",
                "peak_daily_milk": "maximum aggregate litres across persisted animal/day milk records",
                "treatment_rate": "distinct treated animals divided by active animals for the period",
                "feed_conversion": "not calculated: persisted feed quantities are as-fed kg, while scientifically valid feed conversion requires observed DMI",
                "feed_cost_per_litre": "persisted FEED expense divided by persisted milk litres",
                "labour_per_litre": "persisted LABOUR expense divided by persisted milk litres",
                "conception_rate": "confirmed conceptions divided by services with a documented pregnancy diagnosis outcome",
                "confirmed_pregnancies": "one confirmed conception per insemination with documented positive pregnancy evidence; repeated positive checks do not create additional conceptions",
            },
        },
        "methodology": {
            "source": "persisted operational repositories",
            "synthetic_values": False,
            "derived_values": "calculated only when required persisted inputs exist",
            "unsupported_without_history": ["mortality_rate", "culling_rate", "persistency", "feed_conversion"],
        },
