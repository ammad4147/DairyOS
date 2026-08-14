"""Operational lifecycle services for reproduction and nutrition planning."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.herd.reproduction.services.reproductive_event_classifier import (
    classify_animal_state,
)

router = APIRouter(prefix="/farm", tags=["farm-planning"])


class RationPlan(BaseModel):
    plan_id: str
    name: str
    target_group: str
    ingredients: list[dict[str, float | str]] = Field(min_length=1)
    dry_matter_kg: float | None = None
    crude_protein_pct: float | None = None
    ndf_pct: float | None = None
    energy_mcal: float | None = None
    active: bool = True
    farm_id: str = "DEFAULT"


@router.get("/animals/{animal_id}/reproduction")
def reproductive_status(animal_id: str):
    factory = RepositoryFactory.create()
    try:
        if factory.animal().get_by_animal_id(animal_id) is None:
            raise HTTPException(status_code=404, detail="Animal not found")
        events = [x for x in factory.breeding().get_all() if x.animal_id == animal_id]
        events.sort(key=lambda x: x.timestamp or datetime.min)
        classified = classify_animal_state(events)
        return {
            "animal_id": animal_id,
            "data_status": "LIVE_PERSISTED",
            **classified,
            "events": [
                {"event_type": x.event_type, "result": x.result, "timestamp": x.timestamp, "technician": x.technician}
                for x in events
            ],
        }
    finally:
        factory.close()


@router.get("/nutrition/rations")
def list_rations(farm_id: str = "DEFAULT"):
    factory = RepositoryFactory.create()
    try:
        model = factory.session.query(OperationalStateModel).filter(OperationalStateModel.farm_id == farm_id).first()
        plans = [] if model is None else (model.state_payload or {}).get("ration_plans", [])
        return {"data_status": "LIVE_PERSISTED" if plans else "NO_RATION_PLANS", "plans": plans}
    finally:
        factory.close()


@router.post("/nutrition/rations")
def save_ration(plan: RationPlan):
    factory = RepositoryFactory.create()
    try:
        model = factory.session.query(OperationalStateModel).filter(OperationalStateModel.farm_id == plan.farm_id).first()
        if model is None:
            model = OperationalStateModel(farm_id=plan.farm_id, operational_date=datetime.utcnow().date(), state_payload={}, created_at=datetime.utcnow())
            factory.session.add(model)
        payload = dict(model.state_payload or {})
        plans = [p for p in payload.get("ration_plans", []) if p.get("plan_id") != plan.plan_id]
        plans.append(plan.model_dump())
        payload["ration_plans"] = plans
        model.state_payload = payload
        factory.session.commit()
        return {"data_status": "PERSISTED", "plan": plan.model_dump()}
    finally:
        factory.close()
