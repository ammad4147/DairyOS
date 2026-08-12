"""Persisted heat-stress intelligence and actionable risk assessment."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.repositories.repository_factory import RepositoryFactory

router = APIRouter(prefix="/farm", tags=["heat-stress-intelligence"])


class HeatStressIntelligenceObservation(BaseModel):
    temperature_c: float
    humidity_pct: float = Field(ge=0, le=100)
    observed_at: datetime | None = None
    recorded_by: str | None = None
    farm_id: str = "DEFAULT"


def _thi(temperature_c: float, humidity_pct: float) -> float:
    return (1.8 * temperature_c + 32) - ((0.55 - 0.0055 * humidity_pct) * (1.8 * temperature_c - 26.8))


def _risk(thi: float) -> str:
    if thi < 68:
        return "NORMAL"
    if thi < 72:
        return "ALERT"
    if thi < 80:
        return "HIGH"
    return "SEVERE"


def _action(risk: str) -> str:
    return {
        "NORMAL": "Continue routine heat monitoring.",
        "ALERT": "Increase water access checks, shade checks and observation frequency.",
        "HIGH": "Activate heat-abatement measures and increase animal monitoring frequency.",
        "SEVERE": "Immediate heat-abatement response; prioritize vulnerable and high-producing animals.",
    }[risk]


def _model(factory, farm_id: str) -> OperationalStateModel:
    model = factory.session.query(OperationalStateModel).filter(
        OperationalStateModel.farm_id == farm_id
    ).first()
    if model is None:
        model = OperationalStateModel(
            farm_id=farm_id,
            operational_date=datetime.now(timezone.utc).date(),
            state_payload={},
            created_at=datetime.now(timezone.utc),
        )
        factory.session.add(model)
        factory.session.flush()
    return model


@router.post("/heat-stress/intelligence/observations")
def record_observation(observation: HeatStressIntelligenceObservation):
    if observation.temperature_c < -20 or observation.temperature_c > 60:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Temperature outside operational range")
    observed_at = observation.observed_at or datetime.now(timezone.utc)
    thi = round(_thi(observation.temperature_c, observation.humidity_pct), 2)
    risk = _risk(thi)
    factory = RepositoryFactory.create()
    try:
        model = _model(factory, observation.farm_id)
        payload = dict(model.state_payload or {})
        history = list(payload.get("heat_stress_observations", []))
        history.append({
            "observed_at": observed_at.isoformat(),
            "temperature_c": observation.temperature_c,
            "humidity_pct": observation.humidity_pct,
            "thi": thi,
            "risk": risk,
            "recorded_by": observation.recorded_by,
        })
        history.sort(key=lambda item: item.get("observed_at", ""))
        payload["heat_stress_observations"] = history[-500:]
        model.state_payload = payload
        factory.session.commit()
        return {"data_status": "PERSISTED", **history[-1]}
    finally:
        factory.close()


@router.get("/heat-stress/intelligence")
def heat_stress_intelligence(
    farm_id: str = "DEFAULT",
    days: int = Query(default=7, ge=1, le=30),
):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    factory = RepositoryFactory.create()
    try:
        model = factory.session.query(OperationalStateModel).filter(
            OperationalStateModel.farm_id == farm_id
        ).first()
        raw = [] if model is None else list((model.state_payload or {}).get("heat_stress_observations", []))
        observations = []
        for item in raw:
            try:
                observed_at = datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00"))
                if observed_at.tzinfo is None:
                    observed_at = observed_at.replace(tzinfo=timezone.utc)
                if observed_at >= cutoff:
                    observations.append({**item, "observed_at": observed_at})
            except (KeyError, TypeError, ValueError):
                continue
        observations.sort(key=lambda item: item["observed_at"])
        if not observations:
            return {
                "data_status": "NO_ENVIRONMENTAL_OBSERVATION",
                "farm_id": farm_id,
                "period_days": days,
                "observation_count": 0,
                "latest": None,
                "summary": None,
                "actions": [],
            }
        latest = observations[-1]
        thi_values = [float(item["thi"]) for item in observations]
        counts = {risk: sum(1 for item in observations if item.get("risk") == risk) for risk in ("NORMAL", "ALERT", "HIGH", "SEVERE")}
        consecutive_elevated = 0
        for item in reversed(observations):
            if item.get("risk") in {"ALERT", "HIGH", "SEVERE"}:
                consecutive_elevated += 1
            else:
                break
        latest_risk = str(latest.get("risk") or _risk(float(latest["thi"])))
        actions = [] if latest_risk == "NORMAL" else [_action(latest_risk)]
        if consecutive_elevated >= 3:
            actions.append("Sustained heat exposure detected across the latest three observations; verify mitigation effectiveness.")
        return {
            "data_status": "LIVE_PERSISTED",
            "farm_id": farm_id,
            "period_days": days,
            "observation_count": len(observations),
            "latest": {
                **latest,
                "observed_at": latest["observed_at"].isoformat(),
            },
            "summary": {
                "average_thi": round(sum(thi_values) / len(thi_values), 2),
                "maximum_thi": round(max(thi_values), 2),
                "risk_counts": counts,
                "consecutive_elevated_observations": consecutive_elevated,
                "current_risk": latest_risk,
                "alert": latest_risk in {"ALERT", "HIGH", "SEVERE"},
            },
            "actions": actions,
            "definitions": {
                "thi": "Temperature-Humidity Index using the standard dairy THI equation.",
                "risk_bands": "NORMAL <68; ALERT 68-71.99; HIGH 72-79.99; SEVERE >=80.",
                "data_status": "Only persisted environmental observations in the requested period are used.",
            },
        }
    finally:
        factory.close()
