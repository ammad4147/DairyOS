from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends

from dairyos.api.dependencies import get_container
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from dairyos.api.farm_planning import (
    _current_state_api_value,
    _resolve_current_reproductive_state,
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
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def _vaccination_dashboard_counts(container, operational_date: date) -> tuple[int, int]:
    """Project completed and currently-due vaccination records from the journal."""
    completed = 0
    due = 0

    for event in container.event_journal.all_events():
        if event.name != "OperationalInputReceived":
            continue

        event_payload = dict(event.payload or {})
        if str(event_payload.get("input_type") or "").lower() != "vaccination":
            continue

        if str(event_payload.get("status") or "COMPLETED").upper() == "VOID":
            continue

        completed += 1
        next_due_date = _record_day(event_payload.get("next_due_date"))
        if next_due_date is not None and next_due_date <= operational_date:
            due += 1

    return completed, due


@router.get("/dashboard")
def get_dashboard(container=Depends(get_container)):
    """Return the established Dashboard contract from persisted runtime data."""
    payload = container.dashboard_projection_service.project_api_contract(container)

    animal_repository = container.animal_repository

    finance_repository = (
        container.finance_repository
        if hasattr(container, "finance_repository")
        else container.repository_factory.finance()
    )

    active_animals = animal_repository.active_animals()
    finance_rows = finance_repository.get_all()

    receivable_rows = [
        row
        for row in finance_rows
        if str(row.status or "").upper() == "RECEIVABLE"
    ]

    receivables = sum(
        float(row.amount or 0)
        for row in receivable_rows
    )

    operational_date = OperationalDateAuthority(
        repository_factory=container.repository_factory,
    ).current_date()

    completed_vaccinations, due_vaccinations = _vaccination_dashboard_counts(
        container,
        operational_date,
    )

    # Health and reproduction cards are live projections from the same
    # persisted ledgers used by their operational tabs. Event creation must be
    # visible on the Dashboard without relying on stale in-memory state.
    health_cases = container.repository_factory.health_cases().get_all()
    open_health_cases = [
        case
        for case in health_cases
        if str(getattr(case, "status", "") or "").upper() != "RESOLVED"
    ]
    health_observations = container.repository_factory.health().get_all()

    open_health_animals = {
        str(getattr(case, "animal_id", ""))
        for case in open_health_cases
        if getattr(case, "animal_id", None)
    }
    mastitis_animals = {
        str(getattr(case, "animal_id", ""))
        for case in open_health_cases
        if "MASTITIS" in str(
            getattr(case, "diagnosis", "") or ""
        ).upper()
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

    breeding_records = container.repository_factory.breeding().get_all()
    records_by_animal = {}
    for record in breeding_records:
        records_by_animal.setdefault(str(record.animal_id), []).append(record)

    reproduction_counts = {
        "onHeat": 0,
        "inseminated": 0,
        "pregnant": 0,
    }
    for animal_id, records in records_by_animal.items():
        try:
            state = _current_state_api_value(
                _resolve_current_reproductive_state(animal_id, records)
            )
        except (TypeError, ValueError):
            continue
        if state == "HEAT_OBSERVED":
            reproduction_counts["onHeat"] += 1
        elif state == "INSEMINATED":
            reproduction_counts["inseminated"] += 1
        elif state == "PREGNANT":
            reproduction_counts["pregnant"] += 1

    milk_service = MilkProductionTrendIntelligenceService(
        repository_factory=container.repository_factory,
    )

    milk_records = milk_service.milk().get_all()

    all_milk_animals = milk_service._eligible_animals(
        container.repository_factory
    )

    milk_histories = milk_service._animal_histories(
        container.repository_factory,
        all_milk_animals,
    )

    milking_population = milk_service._governed_milking_animals(
        all_milk_animals,
        milk_histories,
        milk_service._schedule_service,
        operational_date,
    )

    milking_population_ids = {
        str(getattr(animal, "animal_id", ""))
        for animal in milking_population
    }

    milk_repo = container.repository_factory.milk()

    # ---------------------------------------------------------------
    # Today's actual recorded milk by current milking animal.
    #
    # This deliberately does NOT require the animal's milking day
    # to be complete. A currently milking cow remains in the current
    # milking population even when only some sessions have been
    # recorded so far.
    # ---------------------------------------------------------------
    ledger_total_by_animal: dict[str, float] = {}

    for animal_id in milking_population_ids:
        row = milk_repo.ledger_row_for_animal_day(
            animal_id,
            operational_date,
        )

        if row is None:
            continue

        status = str(
            getattr(row, "status", "RECORDED") or "RECORDED"
        ).upper()

        if status == "VOID":
            continue

        if row.total_yield is not None:
            ledger_total_by_animal[animal_id] = float(
                row.total_yield
            )

    current_milking_ids = set(ledger_total_by_animal)

    average_yield_per_cow = (
        round(
            sum(ledger_total_by_animal.values())
            / len(ledger_total_by_animal),
            2,
        )
        if ledger_total_by_animal
        else None
    )

    milking_population_count = len(milking_population)
    current_milking_count = len(current_milking_ids)

    milking_percentage = (
        round(
            (current_milking_count / milking_population_count) * 100.0,
            2,
        )
        if milking_population_count
        else None
    )

    # ---------------------------------------------------------------
    # Milk-drop findings remain authoritative from persisted findings.
    # ---------------------------------------------------------------
    findings = (
        container.repository_factory
        .operational_findings()
        .get_open_by_module("MILK")
    )

    yield_drop_watchlist = [
        {
            "finding_id": finding.finding_id,
            "animal_id": finding.subject_id,
            "severity": finding.severity,
            "title": finding.title,
            "detail": finding.detail,
            "status": finding.status,
            "route": finding.route,
            "observation_count": finding.observation_count,
            "alert_color": (
                "RED"
                if finding.severity == "CRITICAL"
                else "AMBER"
            ),
        }
        for finding in findings
        if finding.subject_type == "ANIMAL"
        and finding.dedupe_key
        and finding.dedupe_key.startswith("MILK_DAILY_DROP:")
        and finding.severity in {"HIGH", "CRITICAL"}
    ]

    # ---------------------------------------------------------------
    # Live farm trends.
    #
    # get_trend_analysis() now returns actual persisted observations,
    # including a partial current day. Comparison logic remains
    # completion-aware inside the trend service.
    # ---------------------------------------------------------------
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

    thirty_day_trend = trends["30d"]
    thirty_day_series = list(
        thirty_day_trend.get("series") or []
    )

    current_total = None
    prior_total = None

    if thirty_day_series:
        current_point = next(
            (
                item
                for item in reversed(thirty_day_series)
                if str(item.get("date", ""))
                == operational_date.isoformat()
            ),
            None,
        )

        if current_point is not None:
            current_total = current_point.get("total_yield")

        # Current-day trend may be partial. Only use the
        # previous actual observation for display, while the
        # trend service separately determines whether a valid
        # comparison is permissible.
        prior_points = [
            item
            for item in thirty_day_series
            if str(item.get("date", "")) < operational_date.isoformat()
        ]

        if prior_points:
            prior_total = prior_points[-1].get("total_yield")

    variance_percentage = None

    if (
        prior_total not in (None, 0)
        and current_total is not None
    ):
        variance_percentage = round(
            (
                (float(current_total) - float(prior_total))
                / float(prior_total)
            ) * 100.0,
            1,
        )

    severity = _drop_severity(variance_percentage)

    production_drop = {
        "production_date": operational_date.isoformat(),
        "drop_percentage": (
            abs(variance_percentage)
            if (
                variance_percentage is not None
                and variance_percentage < 0
            )
            else 0.0
        ),
        "variance_percentage": variance_percentage,
        "severity": severity,
        "alert_color": severity,
        "prior_total_litres": prior_total,
        "current_total_litres": current_total,
    }

    # ---------------------------------------------------------------
    # Current-month production from persisted MilkProduction rows.
    # VOID rows excluded.
    # Partial-day production remains visible.
    # ---------------------------------------------------------------
    month_start = operational_date.replace(day=1)
    current_month_production = 0.0

    for record in milk_records:
        status = str(
            getattr(record, "status", "RECORDED") or "RECORDED"
        ).upper()

        if status == "VOID":
            continue

        record_day = _record_day(
            getattr(record, "production_date", None)
        )

        if record_day is None:
            record_day = _record_day(
                getattr(record, "recorded_at", None)
            )

        if record_day is None:
            continue

        if month_start <= record_day <= operational_date:
            total_yield = getattr(
                record,
                "total_yield",
                None,
            )

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

    current_month_production = round(
        current_month_production,
        3,
    )

    # ---------------------------------------------------------------
    # Production extremes for today's actually recorded current
    # milking animals.
    # ---------------------------------------------------------------
    production_points = [
        {
            "date": operational_date.isoformat(),
            "animal_id": animal_id,
            "total_litres": round(value, 2),
            "complete": False,
        }
        for animal_id, value
        in sorted(ledger_total_by_animal.items())
    ]

    highest = (
        max(
            production_points,
            key=lambda item: item["total_litres"],
        )
        if production_points
        else None
    )

    lowest = (
        min(
            production_points,
            key=lambda item: item["total_litres"],
        )
        if production_points
        else None
    )

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
        "completed_vaccinations": completed_vaccinations,
        "due_vaccinations": due_vaccinations,
        "data_status": "LIVE_PERSISTED_DATA",
    }
    payload["reproduction"] = {
        **reproduction_counts,
        "on_heat": reproduction_counts["onHeat"],
        "data_status": "LIVE_PERSISTED_DATA",
    }

    payload["milk"] = {
        "total_production_liters": current_month_production,
        "current_month_production": current_month_production,
        "data_status": "LIVE_PERSISTED_DATA",
        "production_extremes": {
            "highest": highest,
            "lowest": lowest,
            "population_count": current_milking_count,
        },
        "yield_drop_watchlist": yield_drop_watchlist,
        "total_farm_yield_trend": trends,
        "production_drop": production_drop,
        "milking_population_count": milking_population_count,
        "current_milking_count": current_milking_count,
        "milking_percentage": milking_percentage,
        "average_yield_per_cow": average_yield_per_cow,
    }

    return payload
