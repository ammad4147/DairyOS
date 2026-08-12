"""Operational lifecycle services for reproduction and nutrition planning."""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.repositories.repository_factory import RepositoryFactory

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
        state = "UNKNOWN"
        last_heat = None
        last_ai = None
        pregnancy_result = None
        calving = None
        for event in events:
            kind = str(event.event_type or "").upper()
            if kind in {"HEAT_DETECTED", "HEAT_OBSERVED"}:
                state = "HEAT_OBSERVED"
                last_heat = event.timestamp
            elif kind in {"AI", "INSEMINATION", "ARTIFICIAL_INSEMINATION"}:
                state = "INSEMINATED"
                last_ai = event.timestamp
            elif kind in {"PREGNANCY_CONFIRMED", "PREGNANCY"} and str(event.result or "").upper() not in {"NEGATIVE", "NO"}:
                state = "PREGNANT"
                pregnancy_result = event.result
            elif kind in {"PREGNANCY_NEGATIVE", "PREGNANCY_DIAGNOSIS"} and str(event.result or "").upper() in {"NEGATIVE", "NO"}:
                state = "OPEN"
                pregnancy_result = event.result
            elif kind == "CALVING":
                state = "CALVED"
                calving = event.timestamp
            elif kind == "DRY_OFF":
                state = "DRY_OFF"
        expected_calving = None
        if last_ai and state in {"INSEMINATED", "PREGNANT"}:
            expected_calving = (last_ai + timedelta(days=283)).isoformat()
        return {
            "animal_id": animal_id,
            "data_status": "LIVE_PERSISTED",
            "state": state,
            "last_heat": last_heat,
            "last_insemination": last_ai,
            "pregnancy_result": pregnancy_result,
            "expected_calving": expected_calving,
            "last_calving": calving,
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
