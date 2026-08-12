"""Persisted animal-welfare observations and transparent KPI aggregation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.repositories.repository_factory import RepositoryFactory

router = APIRouter(prefix="/farm", tags=["animal-welfare"])


class AnimalWelfareObservation(BaseModel):
    animal_id: str
    welfare_domain: str = Field(default="GENERAL", min_length=1)
    score: float = Field(ge=0, le=100)
    status: str = Field(default="OBSERVED", min_length=1)
    notes: str | None = None
    observed_at: datetime | None = None
    recorded_by: str | None = None
    farm_id: str = "DEFAULT"


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


def _load(factory, farm_id: str) -> list[dict]:
    model = factory.session.query(OperationalStateModel).filter(
        OperationalStateModel.farm_id == farm_id
    ).first()
    if model is None:
        return []
    return list((model.state_payload or {}).get("animal_welfare_observations", []))


@router.post("/welfare/observations")
def record_welfare_observation(observation: AnimalWelfareObservation):
    if not observation.animal_id.strip():
        raise HTTPException(status_code=422, detail="animal_id is required")
    observed_at = observation.observed_at or datetime.now(timezone.utc)
    factory = RepositoryFactory.create()
    try:
        model = _model(factory, observation.farm_id)
        history = list((model.state_payload or {}).get("animal_welfare_observations", []))
        item = {
            "animal_id": observation.animal_id,
            "welfare_domain": observation.welfare_domain.strip().upper(),
            "score": float(observation.score),
            "status": observation.status.strip().upper(),
            "notes": observation.notes,
            "observed_at": observed_at.isoformat(),
            "recorded_by": observation.recorded_by,
        }
        history.append(item)
        history.sort(key=lambda row: row.get("observed_at", ""))
        payload = dict(model.state_payload or {})
        payload["animal_welfare_observations"] = history[-1000:]
        model.state_payload = payload
        factory.session.commit()
        return {"data_status": "PERSISTED", **item}
    finally:
        factory.close()


@router.get("/welfare/overview")
@router.get("/welfare")
def welfare_overview(
    farm_id: str = "DEFAULT",
    days: int = Query(default=30, ge=1, le=365),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    factory = RepositoryFactory.create()
    try:
        raw = _load(factory, farm_id)
        observations: list[dict] = []
        for item in raw:
            try:
                observed_at = datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00"))
                if observed_at.tzinfo is None:
                    observed_at = observed_at.replace(tzinfo=timezone.utc)
                if observed_at >= cutoff:
                    observations.append({**item, "observed_at": observed_at})
            except (KeyError, TypeError, ValueError):
                continue
        observations.sort(key=lambda row: row["observed_at"])
        if not observations:
            return {
                "data_status": "NO_DATA",
                "farm_id": farm_id,
                "period_days": days,
                "observation_count": 0,
                "animals_observed": 0,
                "latest": None,
                "summary": None,
                "alerts": [],
            }

        scores = [float(row["score"]) for row in observations]
        alerts = [row for row in observations if float(row["score"]) < 50 or str(row.get("status")) in {"ALERT", "CRITICAL"}]
        animals = {str(row["animal_id"]) for row in observations}
        domain_counts: dict[str, int] = {}
        for row in observations:
            domain = str(row.get("welfare_domain") or "GENERAL")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        latest = observations[-1]
        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "farm_id": farm_id,
            "period_days": days,
            "observation_count": len(observations),
            "animals_observed": len(animals),
            "latest": {**latest, "observed_at": latest["observed_at"].isoformat()},
            "summary": {
                "average_score": round(sum(scores) / len(scores), 2),
                "minimum_score": round(min(scores), 2),
                "maximum_score": round(max(scores), 2),
                "welfare_alert_count": len(alerts),
                "welfare_alert_rate_percent": round((len(alerts) / len(observations)) * 100, 2),
                "domain_observation_counts": domain_counts,
            },
            "alerts": [
                {**row, "observed_at": row["observed_at"].isoformat()}
                for row in alerts[-20:]
            ],
            "definitions": {
                "score": "Observed welfare score on a 0-100 scale supplied by the operator; DairyOS does not invent scores.",
                "alert": "An observation is an alert when its supplied score is below 50 or its supplied status is ALERT/CRITICAL.",
                "data_status": "Only persisted observations inside the requested period are aggregated.",
            },
        }

    finally:
        factory.close()
