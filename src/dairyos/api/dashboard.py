from datetime import timedelta

from fastapi import APIRouter, Depends

from dairyos.api.dependencies import get_container
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)


router = APIRouter(
    tags=["Dashboard"],
)


def _drop_severity(variance_percentage: float | None) -> str | None:
    if variance_percentage is None or variance_percentage >= -10.0:
        return None
    if variance_percentage >= -20.0:
        return "AMBER"
    return "RED"


@router.get("/dashboard")
def get_dashboard(
    container=Depends(get_container),
):
    """Return the established dashboard contract from persisted runtime data."""
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
        row for row in finance_rows
        if str(row.status or "").upper() == "RECEIVABLE"
    ]
    receivables = sum(float(row.amount or 0) for row in receivable_rows)

    operational_date = OperationalDateAuthority().current_date()
    milk_service = MilkProductionTrendIntelligenceService(
        repository_factory=container.repository_factory,
    )
    milk_records = milk_service.milk().get_all()
    milk_animals = milk_service._eligible_animals(container.repository_factory)
    milk_histories = milk_service._animal_histories(container.repository_factory, milk_animals)

    daily_snapshots = []
    for animal in milk_animals:
        snapshot = milk_service._daily_animal_snapshot(
            milk_records,
            animal,
            milk_histories.get(str(animal.animal_id), []),
            operational_date,
        )
        if snapshot and snapshot.get("complete"):
            daily_snapshots.append(snapshot)

    daily_snapshots.sort(key=lambda item: item["total_litres"])

    findings = container.repository_factory.operational_findings().get_open_by_module("MILK")
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
            "alert_color": "RED" if finding.severity == "CRITICAL" else "AMBER",
        }
        for finding in findings
        if finding.subject_type == "ANIMAL"
        and finding.dedupe_key
        and finding.dedupe_key.startswith("MILK_DAILY_DROP:")
        and finding.severity in {"HIGH", "CRITICAL"}
    ]

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
    prior_total = thirty_day_trend.get("prior_total_litres")
    current_total = thirty_day_trend.get("daily_total")
    variance_percentage = None
    if prior_total not in (None, 0) and current_total is not None:
        variance_percentage = round(
            ((current_total - prior_total) / prior_total) * 100.0,
            1,
        )

    severity = _drop_severity(variance_percentage)
    production_drop = {
        "production_date": operational_date.isoformat(),
        "drop_percentage": abs(variance_percentage) if variance_percentage is not None and variance_percentage < 0 else 0.0,
        "variance_percentage": variance_percentage,
        "severity": severity,
        "alert_color": severity,
        "prior_total_litres": prior_total,
        "current_total_litres": current_total,
    }

    expected_milking_count = len(active_animals)
    complete_count = len(daily_snapshots)
    average_yield_per_cow = (
        round(sum(snapshot["total_litres"] for snapshot in daily_snapshots) / complete_count, 2)
        if complete_count
        else None
    )
    milking_percentage = (
        round((complete_count / expected_milking_count) * 100.0, 2)
        if expected_milking_count
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
    payload["milk"] = {
        "data_status": "LIVE_PERSISTED_DATA",
        "production_extremes": {
            "highest": daily_snapshots[-1] if daily_snapshots else None,
            "lowest": daily_snapshots[0] if daily_snapshots else None,
            "population_count": complete_count,
        },
        "yield_drop_watchlist": yield_drop_watchlist,
        "total_farm_yield_trend": trends,
        "production_drop": production_drop,
        "milking_percentage": milking_percentage,
        "average_yield_per_cow": average_yield_per_cow,
    }
    return payload
