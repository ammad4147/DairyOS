from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends

from dairyos.api.dashboard_attention import project_vaccination_schedule
from dairyos.api.dependencies import get_container
from dairyos.api.farm_planning import (
    _current_state_api_value,
    _resolve_current_reproductive_state,
)
from dairyos.api.milk_production_analytics import (
    _production_extremes,
    _yield_drop_watchlist,
)
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (  # noqa: E501
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.reproduction.services.post_calving_return_service import (
    reconcile_due_post_calving_returns,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)

router = APIRouter(tags=["Dashboard"])


def _drop_severity(variance_percentage: float | None) -> str | None:
    if variance_percentage is None or variance_percentage >= -10.0:
        return None
    if variance_percentage >= -20.0:
        return "AMBER"
    return "RED"


def _record_day(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _vaccination_dashboard_projection(
    container,
    operational_date: date,
    active_animal_ids: set[str] | None = None,
):
    """Project current vaccination schedules from the durable event journal."""
    return project_vaccination_schedule(
        container.event_journal.all_events(),
        operational_date,
        active_animal_ids=active_animal_ids,
    )


def _vaccination_dashboard_counts(
    container,
    operational_date: date,
    active_animal_ids: set[str] | None = None,
) -> tuple[int, int]:
    """Keep the legacy counts while deriving due work from current schedules."""
    projection = _vaccination_dashboard_projection(
        container,
        operational_date,
        active_animal_ids=active_animal_ids,
    )
    return int(projection["completed"]), len(projection["due"])


_HEALTH_SEVERITY_RANK = {
    "CRITICAL": 5,
    "SEVERE": 4,
    "HIGH": 4,
    "MODERATE": 3,
    "MEDIUM": 3,
    "LOW": 2,
    "NORMAL": 1,
}


def _health_dashboard_animals(
    cases,
    operational_date: date,
    active_animal_ids: set[str] | None = None,
) -> list[dict]:
    """Return one current open-case row per active animal for the dashboard."""
    latest: dict[str, tuple[tuple, dict]] = {}
    for position, case in enumerate(cases):
        if str(getattr(case, "status", "") or "").upper() == "RESOLVED":
            continue
        animal_id = str(getattr(case, "animal_id", "") or "").strip()
        if not animal_id:
            continue
        if active_animal_ids is not None and animal_id not in active_animal_ids:
            continue

        severity = str(getattr(case, "severity", "") or "NORMAL").upper()
        opened_at = getattr(case, "opened_at", None)
        opened_day = _record_day(opened_at) or date.min
        follow_up = getattr(case, "follow_up_due_at", None)
        follow_up_day = _record_day(follow_up)
        row = {
            "animal_id": animal_id,
            "diagnosis": str(getattr(case, "diagnosis", "") or "Unspecified"),
            "severity": severity,
            "opened_at": (
                opened_at.isoformat()
                if isinstance(opened_at, datetime)
                else str(opened_at or "")
            ),
            "follow_up_due_at": (
                follow_up.isoformat()
                if isinstance(follow_up, datetime)
                else str(follow_up or "")
            ),
        }
        rank = (
            _HEALTH_SEVERITY_RANK.get(severity, 1),
            1 if follow_up_day is not None and follow_up_day <= operational_date else 0,
            opened_day,
            position,
        )
        previous = latest.get(animal_id)
        if previous is None or rank > previous[0]:
            latest[animal_id] = (rank, row)

    rows = [row for _, row in latest.values()]
    rows.sort(
        key=lambda item: (
            -_HEALTH_SEVERITY_RANK.get(str(item["severity"]).upper(), 1),
            item["follow_up_due_at"] or "9999-12-31",
            item["animal_id"],
        )
    )
    return rows


@router.get("/dashboard")
def get_dashboard(container=Depends(get_container)):
    """Return the established Dashboard contract from persisted runtime data."""
    reconcile_due_post_calving_returns(
        container.repository_factory,
        container.event_journal,
    )
    payload = container.dashboard_projection_service.project_api_contract(container)
    animal_repository = container.animal_repository
    finance_repository = (
        container.finance_repository
        if hasattr(container, "finance_repository")
        else container.repository_factory.finance()
    )
    active_animals = animal_repository.active_animals()
    active_animal_ids = {
        str(getattr(animal, "animal_id", "") or "").strip()
        for animal in active_animals
        if getattr(animal, "animal_id", None)
    }
    finance_rows = finance_repository.get_all()
    receivable_rows = [
        row for row in finance_rows
        if str(row.status or "").upper() == "RECEIVABLE"
    ]
    receivables = sum(float(row.amount or 0) for row in receivable_rows)

    operational_date = OperationalDateAuthority(
        repository_factory=container.repository_factory,
    ).current_date()
    vaccination_projection = _vaccination_dashboard_projection(
        container,
        operational_date,
        active_animal_ids=active_animal_ids,
    )
    completed_vaccinations = int(vaccination_projection["completed"])
    due_vaccinations = len(vaccination_projection["due"])

    health_cases = container.repository_factory.health_cases().get_all()
    open_health_cases = [
        case for case in health_cases
        if str(getattr(case, "status", "") or "").upper() != "RESOLVED"
    ]
    health_observations = container.repository_factory.health().get_all()
    open_health_animals = {
        str(getattr(case, "animal_id", ""))
        for case in open_health_cases if getattr(case, "animal_id", None)
    }
    mastitis_animals = {
        str(getattr(case, "animal_id", ""))
        for case in open_health_cases
        if "MASTITIS" in str(getattr(case, "diagnosis", "") or "").upper()
    }
    high_temperature_animals = {
        str(getattr(observation, "animal_id", ""))
        for observation in health_observations
        if float(
            getattr(observation, "temperature_c", None)
            or getattr(observation, "temperature", None)
            or 0.0
        ) >= 39.5
    }
    health_dashboard_animals = _health_dashboard_animals(
        open_health_cases,
        operational_date,
        active_animal_ids=active_animal_ids,
    )

    breeding_records = container.repository_factory.breeding().get_all()
    records_by_animal = {}
    for record in breeding_records:
        records_by_animal.setdefault(str(record.animal_id), []).append(record)
    reproduction_counts = {"inseminated": 0, "pregnant": 0}
    for animal_id, records in records_by_animal.items():
        try:
            state = _current_state_api_value(
                _resolve_current_reproductive_state(animal_id, records)
            )
        except (TypeError, ValueError):
            continue
        if state == "INSEMINATED":
            reproduction_counts["inseminated"] += 1
        elif state == "PREGNANT":
            reproduction_counts["pregnant"] += 1

    milk_service = MilkProductionTrendIntelligenceService(
        repository_factory=container.repository_factory,
    )
    milk_records = milk_service.milk().get_all()
    all_milk_animals = milk_service._eligible_animals(container.repository_factory)
    milk_histories = milk_service._animal_histories(
        container.repository_factory, all_milk_animals
    )
    milking_population = milk_service._governed_milking_animals(
        all_milk_animals,
        milk_histories,
        milk_service._schedule_service,
        operational_date,
    )
    milking_population_ids = {
        str(getattr(animal, "animal_id", "")) for animal in milking_population
    }
    milk_repo = container.repository_factory.milk()

    ledger_total_by_animal: dict[str, float] = {}
    for animal_id in milking_population_ids:
        row = milk_repo.ledger_row_for_animal_day(animal_id, operational_date)
        if row is None:
            continue
        status = str(getattr(row, "status", "RECORDED") or "RECORDED").upper()
        if status == "VOID":
            continue
        if row.total_yield is not None:
            ledger_total_by_animal[animal_id] = float(row.total_yield)

    current_milking_ids = set(ledger_total_by_animal)
    average_yield_per_cow = (
        round(sum(ledger_total_by_animal.values()) / len(ledger_total_by_animal), 2)
        if ledger_total_by_animal else None
    )
    milking_population_count = len(milking_population)
    current_milking_count = len(current_milking_ids)
    milking_percentage = (
        round((current_milking_count / milking_population_count) * 100.0, 2)
        if milking_population_count else None
    )

    # Dashboard and Milk API now use the same persisted-production derivation.
    yield_drop_watchlist = _yield_drop_watchlist(
        service=milk_service,
        records=milk_records,
        animals=all_milk_animals,
        histories=milk_histories,
        target_date=operational_date,
        lookback_days=30,
    )
    production_extremes = _production_extremes(
        service=milk_service,
        records=milk_records,
        animals=all_milk_animals,
        histories=milk_histories,
        target_date=operational_date,
    )

    trends = {}
    for days in (7, 15, 30):
        start_date = operational_date - timedelta(days=days - 1)
        trends[f"{days}d"] = milk_service.get_trend_analysis(
            period=f"{days}d",
            start_date=start_date,
            end_date=operational_date,
            anchor_date=operational_date,
            factory=container.repository_factory,
        )

    thirty_day_series = list(trends["30d"].get("series") or [])
    current_total = None
    prior_total = None
    if thirty_day_series:
        current_point = next(
            (
                item for item in reversed(thirty_day_series)
                if str(item.get("date", "")) == operational_date.isoformat()
            ),
            None,
        )
        if current_point is not None:
            current_total = current_point.get("total_yield")
        prior_points = [
            item for item in thirty_day_series
            if str(item.get("date", "")) < operational_date.isoformat()
        ]
        if prior_points:
            prior_total = prior_points[-1].get("total_yield")

    variance_percentage = None
    if prior_total not in (None, 0) and current_total is not None:
        variance_percentage = round(
            ((float(current_total) - float(prior_total)) / float(prior_total)) * 100.0,
            1,
        )
    severity = _drop_severity(variance_percentage)
    production_drop = {
        "production_date": operational_date.isoformat(),
        "drop_percentage": (
            abs(variance_percentage)
            if variance_percentage is not None and variance_percentage < 0
            else 0.0
        ),
        "variance_percentage": variance_percentage,
        "severity": severity,
        "alert_color": severity,
        "prior_total_litres": prior_total,
        "current_total_litres": current_total,
    }

    month_start = operational_date.replace(day=1)
    current_month_production = 0.0
    for record in milk_records:
        status = str(getattr(record, "status", "RECORDED") or "RECORDED").upper()
        if status == "VOID":
            continue
        record_day = _record_day(getattr(record, "production_date", None))
        if record_day is None:
            record_day = _record_day(getattr(record, "recorded_at", None))
        if record_day is None:
            continue
        if month_start <= record_day <= operational_date:
            total_yield = getattr(record, "total_yield", None)
            if total_yield is not None:
                current_month_production += float(total_yield)
            else:
                current_month_production += sum(
                    float(value or 0.0)
                    for value in (
                        getattr(record, "morning_yield", None),
                        getattr(record, "afternoon_yield", None),
                        getattr(record, "evening_yield", None),
                    )
                )
    current_month_production = round(current_month_production, 3)

    dashboard = payload.setdefault("dashboard", {})
    dashboard["finance"] = {
        "receivables": receivables,
        "receivable_count": len(receivable_rows),
    }
    dashboard["animals"] = {
        **dashboard.get("animals", {}),
        "total": len(active_animals),
    }
    payload["animals"] = {
        **payload.get("animals", {}),
        "total": len(active_animals),
    }
    payload["finance"] = dashboard["finance"]
    payload["health"] = {
        "sick": len(open_health_animals),
        "sick_animals": health_dashboard_animals,
        "mastitis": len(mastitis_animals),
        "highTemp": len(high_temperature_animals),
        "completedVax": completed_vaccinations,
        "dueVax": due_vaccinations,
        "active_exceptions": len(open_health_animals),
        "critical_cases": len(mastitis_animals),
        "high_temperature": len(high_temperature_animals),
        "completed_vaccinations": completed_vaccinations,
        "due_vaccinations": due_vaccinations,
        "openCases": len(open_health_cases),
        "data_status": "LIVE_PERSISTED_DATA",
    }
    payload["vaccination"] = {
        "completed": completed_vaccinations,
        "due": due_vaccinations,
        "due_animals": list(vaccination_projection["schedules"]),
        "completed_vaccinations": completed_vaccinations,
        "due_vaccinations": due_vaccinations,
        "data_status": "LIVE_PERSISTED_DATA",
    }
    active_reproductive_cycle = (
        reproduction_counts["inseminated"]
        + reproduction_counts["pregnant"]
    )
    pregnancy_ratio = (
        round(
            (
                reproduction_counts["pregnant"]
                / active_reproductive_cycle
            )
            * 100.0,
            2,
        )
        if active_reproductive_cycle
        else 0.0
    )
    payload["reproduction"] = {
        **reproduction_counts,
        "pregnancyRatio": pregnancy_ratio,
        "pregnancy_ratio_percent": pregnancy_ratio,
        "data_status": "LIVE_PERSISTED_DATA",
    }
    payload["milk"] = {
        "total_production_liters": current_month_production,
        "current_month_production": current_month_production,
        "data_status": "LIVE_PERSISTED_DATA",
        "production_extremes": production_extremes,
        "yield_drop_watchlist": yield_drop_watchlist,
        "total_farm_yield_trend": trends,
        "production_drop": production_drop,
        "milking_population_count": milking_population_count,
        "current_milking_count": current_milking_count,
        "milking_percentage": milking_percentage,
        "average_yield_per_cow": average_yield_per_cow,
    }
    return payload
