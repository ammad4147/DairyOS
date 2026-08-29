from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.api.dependencies import get_container
from dairyos.platform.digital_twin.services.digital_twin_service import DigitalTwinService

router = APIRouter(prefix="/farm/digital-twin", tags=["Digital Twin"])


class ScenarioRequest(BaseModel):
    metric: str = Field(min_length=1)
    scenario_name: str = Field(min_length=1)
    parameter: str = Field(min_length=1)
    change_percent: float
    growth_rate_percent: float = 0.0
    horizon_days: int = Field(default=30, ge=1, le=3650)
    baseline_period_days: int = Field(default=30, ge=1, le=3650)


def _date_value(record, *names):
    for name in names:
        value = getattr(record, name, None)
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    return None


def _baseline(factory, metric: str, days: int):
    metric = metric.upper()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    if metric == "HERD_SIZE":
        animals = factory.animal().get_all()
        active_count = sum(1 for animal in animals if getattr(animal, "active", True))
        return float(active_count), {"active_animals": int(active_count)}
    if metric == "MILK_LITERS":
        records = factory.milk().get_all()
        total = 0.0
        period_records = 0
        for record in records:
            stamp = _date_value(record, "production_date", "created_at")
            if stamp and start <= stamp < end:
                total += float(getattr(record, "total_yield", 0.0) or 0.0)
                period_records += 1
        return total, {"period_start": start.date().isoformat(), "period_end": end.date().isoformat(), "milk_records": period_records}
    if metric == "FEED_KG":
        records = factory.feed().get_all()
        total = 0.0
        period_records = 0
        for record in records:
            stamp = _date_value(record, "feeding_date", "created_at")
            if stamp and start <= stamp < end:
                total += float(getattr(record, "quantity_kg", 0.0) or 0.0)
                period_records += 1
        return total, {"period_start": start.date().isoformat(), "period_end": end.date().isoformat(), "feed_records": period_records}
    raise ValueError("Unsupported Digital Twin metric. Use MILK_LITERS, HERD_SIZE, or FEED_KG.")


@router.get("/baseline")
def digital_twin_baseline(
    metric: str = Query(default="MILK_LITERS"),
    days: int = Query(default=30, ge=1, le=3650),
    container=Depends(get_container),
):
    factory = container.repository_factory
    try:
        value, evidence = _baseline(factory, metric, days)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "metric": metric.upper(),
        "baseline_value": value,
        "baseline_period_days": days,
        "data_status": "LIVE_PERSISTED_DATA",
        "evidence": evidence,
    }


@router.post("/scenario")
def digital_twin_scenario(request: ScenarioRequest, container=Depends(get_container)):
    factory = container.repository_factory
    try:
        baseline, evidence = _baseline(factory, request.metric, request.baseline_period_days)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if baseline == 0 and request.change_percent < 0:
        raise HTTPException(status_code=422, detail="Cannot apply a negative scenario to a zero baseline.")
    result = DigitalTwinService().scenario(
        farm_id="farm",
        metric=request.metric.upper(),
        current_value=baseline,
        scenario_name=request.scenario_name,
        parameter=request.parameter,
        change_percent=request.change_percent,
        growth_rate_percent=request.growth_rate_percent,
        horizon_days=request.horizon_days,
        state={"metric": request.metric.upper(), "baseline": baseline, "evidence": evidence},
    )
    return {
        "data_status": "LIVE_PERSISTED_BASELINE_SCENARIO",
        "metric": request.metric.upper(),
        "baseline_value": baseline,
        "baseline_period_days": request.baseline_period_days,
        "horizon_days": request.horizon_days,
        "growth_rate_percent": request.growth_rate_percent,
        "scenario_change_percent": request.change_percent,
        "scenario_name": request.scenario_name,
        "evidence": evidence,
        "digital_twin": result.__dict__ if hasattr(result, "__dict__") else result,
    }
