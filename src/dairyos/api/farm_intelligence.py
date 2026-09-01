"""Cross-domain operational intelligence endpoints.

Results are derived from persisted repositories. Missing source data is
reported explicitly instead of being fabricated.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.data.database.models.operational_state_model import OperationalStateModel
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.core.time_utils import utcnow
from dairyos.finance.classification.transaction_classifier import is_expense, is_income

router = APIRouter(prefix="/farm", tags=["farm-intelligence"])


class HeatStressObservation(BaseModel):
    temperature_c: float
    humidity_pct: float = Field(ge=0, le=100)
    observed_at: datetime | None = None
    recorded_by: str | None = None
    farm_id: str = "DEFAULT"


class SOPProtocol(BaseModel):
    protocol_id: str
    title: str
    domain: str
    steps: list[str] = Field(min_length=1)
    active: bool = True
    version: int = 1
    farm_id: str = "DEFAULT"


def _json(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _json(item) for key, item in value.items()}
    return value


def _record_dict(record: Any) -> dict[str, Any]:
    fields = (
        "id", "animal_id", "animal_type", "ear_tag", "rfid", "breed", "sex",
        "date_of_birth", "dam_id", "sire_id", "lifecycle_status", "status",
        "is_currently_milking", "milking_frequency", "production_group", "location",
        "active", "created_at", "updated_at", "production_date", "morning_yield",
        "afternoon_yield", "evening_yield", "total_yield", "feeding_date", "feed_type",
        "quantity_kg", "group_or_pen", "observed_at", "observation", "severity", "notes",
        "reported_by", "temperature", "temperature_c", "event_type", "result",
        "technician", "timestamp", "treated_at", "drug_name", "withdrawal_end",
        "transaction_type", "category", "amount", "transaction_date", "reference",
        "currency", "milk_sale_id", "feed_record_id",
    )
    return {field: _json(getattr(record, field)) for field in fields if hasattr(record, field)}


def _factory() -> RepositoryFactory:
    return RepositoryFactory.create()


@router.get("/animals/{animal_id}/passport")
def animal_passport(animal_id: str):
    factory = _factory()
    try:
        animal = factory.animal().get_by_animal_id(animal_id)
        if animal is None:
            raise HTTPException(status_code=404, detail="Animal not found")
        return {
            "animal": _record_dict(animal),
            "lifecycle": {
                "animal_id": animal_id,
                "status": animal.lifecycle_status,
                "active": animal.active,
                "dam_id": animal.dam_id,
                "sire_id": animal.sire_id,
            },
            "milk": [_record_dict(x) for x in factory.milk().get_all() if x.animal_id == animal_id],
            "feed": [_record_dict(x) for x in factory.feed().get_all() if x.animal_id == animal_id],
            "health": [_record_dict(x) for x in factory.health().get_all() if x.animal_id == animal_id],
            "breeding": [_record_dict(x) for x in factory.breeding().get_all() if x.animal_id == animal_id],
            "treatments": [_record_dict(x) for x in factory.treatment().get_by_animal(animal_id)],
            "finance": [_record_dict(x) for x in factory.finance().get_all() if getattr(x, "animal_id", None) == animal_id],
            "passport_status": "LIVE_PERSISTED",
        }
    finally:
        factory.close()


@router.get("/youngstock")
def youngstock():
    factory = _factory()
    try:
        today = utcnow().date()
        result = []
        for animal in factory.animal().get_all():
            if animal.lifecycle_status not in {"CALF", "HEIFER"}:
                continue
            age_days = (today - animal.date_of_birth).days if animal.date_of_birth else None
            result.append({
                "animal_id": animal.animal_id,
                "lifecycle_status": animal.lifecycle_status,
                "age_days": age_days,
                "breed": animal.breed,
                "sex": animal.sex,
                "dam_id": animal.dam_id,
                "sire_id": animal.sire_id,
                "active": animal.active,
            })
        return {"data_status": "LIVE_PERSISTED", "count": len(result), "animals": result}
    finally:
        factory.close()


@router.get("/kpis")
def dairy_kpis(days: int = Query(default=30, ge=1, le=366)):
    cutoff = utcnow() - timedelta(days=days)
    factory = _factory()
    try:
        animals = factory.animal().get_all()
        active = [x for x in animals if x.active]
        milking = [x for x in active if x.is_currently_milking or x.lifecycle_status == "LACTATING"]
        milk = [x for x in factory.milk().get_all() if x.production_date >= cutoff]
        feed = [x for x in factory.feed().get_all() if x.feeding_date >= cutoff]
        finance = [x for x in factory.finance().get_all() if x.transaction_date >= cutoff]
        breeding = factory.breeding().get_all()
        health = [x for x in factory.health().get_all() if x.observed_at >= cutoff]
        treatments = [x for x in factory.treatment().get_all() if x.treated_at >= cutoff]
        litres = sum(float(x.total_yield or 0) for x in milk)
        expenses = sum(float(x.amount or 0) for x in finance if is_expense(x))
        income = sum(float(x.amount or 0) for x in finance if is_income(x))
        inseminations = [x for x in breeding if str(x.event_type).upper() in {"AI", "INSEMINATION", "ARTIFICIAL_INSEMINATION"}]
        pregnancies = [x for x in breeding if str(x.event_type).upper() in {"PREGNANCY_CONFIRMED", "PREGNANCY"} and str(x.result or "").upper() not in {"NEGATIVE", "NO"}]
        return {
            "period_days": days,
            "from": cutoff.isoformat(),
            "to": utcnow().isoformat(),
            "data_status": "LIVE_PERSISTED",
            "values": {
                "herd_size": len(active),
                "milking_animals": len(milking),
                "milk_litres": round(litres, 3),
                "milk_per_milking_animal": round(litres / len(milking), 3) if milking else None,
                "feed_kg": round(sum(float(x.quantity_kg or 0) for x in feed), 3),
                "expenses": round(expenses, 2),
                "income": round(income, 2),
                "net_cash_movement": round(income - expenses, 2),
                "cost_per_litre": round(expenses / litres, 4) if litres else None,
                "health_observations": len(health),
                "treatments": len(treatments),
                "inseminations": len(inseminations),
                "pregnancies_confirmed": len(pregnancies),
                "conception_rate": round(len(pregnancies) / len(inseminations), 4) if inseminations else None,
            },
            "quality": {
                "cost_per_litre": "COMPLETE_FOR_RECORDED_FINANCIAL_EXPENSES" if litres else "NO_MILK_DATA",
                "conception_rate": "CALCULATED_ONLY_WHEN_INSEMINATIONS_EXIST",
            },
        }
    finally:
        factory.close()


@router.post("/heat-stress/observations")
def record_heat_stress(observation: HeatStressObservation):
    if observation.temperature_c < -20 or observation.temperature_c > 60:
        raise HTTPException(status_code=422, detail="Temperature outside operational range")
    thi = (1.8 * observation.temperature_c + 32) - ((0.55 - 0.0055 * observation.humidity_pct) * (1.8 * observation.temperature_c - 26.8))
    risk = "NORMAL" if thi < 68 else "ALERT" if thi < 72 else "HIGH" if thi < 80 else "SEVERE"
    factory = _factory()
    try:
        model = factory.session.query(OperationalStateModel).filter(OperationalStateModel.farm_id == observation.farm_id).first()
        if model is None:
            model = OperationalStateModel(farm_id=observation.farm_id, operational_date=utcnow().date(), state_payload={}, created_at=utcnow())
            factory.session.add(model)
        payload = dict(model.state_payload or {})
        history = list(payload.get("heat_stress_observations", []))
        item = {"observed_at": (observation.observed_at or datetime.now(timezone.utc)).isoformat(), "temperature_c": observation.temperature_c, "humidity_pct": observation.humidity_pct, "thi": round(thi, 2), "risk": risk, "recorded_by": observation.recorded_by}
        history.append(item)
        payload["heat_stress_observations"] = history[-500:]
        model.state_payload = payload
        factory.session.commit()
        return {"data_status": "PERSISTED", **item}
    finally:
        factory.close()


@router.get("/heat-stress")
def heat_stress_status(farm_id: str = "DEFAULT"):
    factory = _factory()
    try:
        model = factory.session.query(OperationalStateModel).filter(OperationalStateModel.farm_id == farm_id).first()
        observations = [] if model is None else (model.state_payload or {}).get("heat_stress_observations", [])
        latest = observations[-1] if observations else None
        return {"data_status": "LIVE_PERSISTED" if latest else "NO_ENVIRONMENTAL_OBSERVATION", "latest": latest, "alert": bool(latest and latest.get("risk") in {"ALERT", "HIGH", "SEVERE"})}
    finally:
        factory.close()


@router.get("/welfare/kpis")
def welfare_kpis(days: int = Query(default=30, ge=1, le=366)):
    cutoff = utcnow() - timedelta(days=days)
    factory = _factory()
    try:
        animals = factory.animal().get_all()
        total = len(animals)
        active = [x for x in animals if x.active]
        health = [x for x in factory.health().get_all() if x.observed_at >= cutoff]
        treatments = [x for x in factory.treatment().get_all() if x.treated_at >= cutoff]
        morbidity_events = [x for x in health if str(x.severity or "NORMAL").upper() not in {"NORMAL", "NONE"}]
        deceased = [x for x in animals if str(x.lifecycle_status or "").upper() == "DECEASED" or (not x.active and str(x.status).upper() == "DECEASED")]
        return {"period_days": days, "data_status": "LIVE_PERSISTED", "values": {"herd_size": total, "active_animals": len(active), "mortality_rate": round(len(deceased) / total, 4) if total else None, "morbidity_events": len(morbidity_events), "morbidity_rate": round(len(morbidity_events) / len(active), 4) if active else None, "treatment_events": len(treatments), "treatment_rate": round(len(treatments) / len(active), 4) if active else None}, "definitions": {"morbidity_rate": "non-NORMAL persisted health observations divided by active animals", "mortality_rate": "persisted DECEASED animals divided by all persisted animals"}}
    finally:
        factory.close()


@router.get("/sops")
def list_sops(farm_id: str = "DEFAULT"):
    factory = _factory()
    try:
        model = factory.session.query(OperationalStateModel).filter(OperationalStateModel.farm_id == farm_id).first()
        protocols = [] if model is None else (model.state_payload or {}).get("sop_protocols", [])
        return {"data_status": "LIVE_PERSISTED" if protocols else "NO_PROTOCOLS", "protocols": protocols}
    finally:
        factory.close()


@router.post("/sops")
def upsert_sop(protocol: SOPProtocol):
    factory = _factory()
    try:
        model = factory.session.query(OperationalStateModel).filter(OperationalStateModel.farm_id == protocol.farm_id).first()
        if model is None:
            model = OperationalStateModel(farm_id=protocol.farm_id, operational_date=utcnow().date(), state_payload={}, created_at=utcnow())
            factory.session.add(model)
        payload = dict(model.state_payload or {})
        protocols = [p for p in payload.get("sop_protocols", []) if p.get("protocol_id") != protocol.protocol_id]
        protocols.append(protocol.model_dump())
        payload["sop_protocols"] = protocols
        model.state_payload = payload
        factory.session.commit()
        return {"data_status": "PERSISTED", "protocol": protocol.model_dump()}
    finally:
        factory.close()
