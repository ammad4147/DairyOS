from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.data.models.feed_ration import FeedRation
from dairyos.data.models.feed_record import FeedRecord
from dairyos.core.time_utils import utcnow

router = APIRouter(prefix="/farm/feed", tags=["feed-nutrition"])


class RationIngredient(BaseModel):
    feed_type: str = Field(min_length=1)
    quantity_kg: float = Field(gt=0)


class RationEntry(BaseModel):
    name: str = Field(min_length=1)
    animal_group: str = Field(min_length=1)
    ingredients: list[RationIngredient] = Field(min_length=1)
    target_dmi_kg: float | None = Field(default=None, gt=0)
    dry_matter_pct: float | None = Field(default=None, gt=0, le=100)
    crude_protein_pct: float | None = Field(default=None, ge=0, le=100)
    ndf_pct: float | None = Field(default=None, ge=0, le=100)
    energy_mcal_kg: float | None = Field(default=None, gt=0)
    cost_per_kg: float | None = Field(default=None, ge=0)
    effective_date: str
    operator: str = Field(min_length=1)


class FeedEntry(BaseModel):
    animal_id: str | None = None
    group_or_pen: str | None = None
    feed_type: str = Field(min_length=1)
    quantity_kg: float = Field(gt=0)
    feeding_date: datetime | None = None
    notes: str | None = None


@router.post("/rations")
def create_ration(payload: RationEntry):
    factory = RepositoryFactory.create()
    try:
        if not payload.animal_group.strip():
            raise HTTPException(status_code=400, detail="animal_group is required")
        record = FeedRation(
            name=payload.name.strip(),
            animal_group=payload.animal_group.strip(),
            ingredients_json=json.dumps([item.model_dump() for item in payload.ingredients], sort_keys=True),
            target_dmi_kg=payload.target_dmi_kg,
            dry_matter_pct=payload.dry_matter_pct,
            crude_protein_pct=payload.crude_protein_pct,
            ndf_pct=payload.ndf_pct,
            energy_mcal_kg=payload.energy_mcal_kg,
            cost_per_kg=payload.cost_per_kg,
            effective_date=payload.effective_date,
            operator=payload.operator.strip(),
        )
        saved = factory.feed_rations().add(record)
        return {
            "id": saved.id,
            "name": saved.name,
            "animal_group": saved.animal_group,
            "ingredients": json.loads(saved.ingredients_json),
            "target_dmi_kg": saved.target_dmi_kg,
            "dry_matter_pct": saved.dry_matter_pct,
            "crude_protein_pct": saved.crude_protein_pct,
            "ndf_pct": saved.ndf_pct,
            "energy_mcal_kg": saved.energy_mcal_kg,
            "cost_per_kg": saved.cost_per_kg,
            "effective_date": saved.effective_date,
            "operator": saved.operator,
            "data_status": "LIVE_PERSISTED_DATA",
        }
    finally:
        factory.close()


@router.get("/rations")
def list_rations(animal_group: str | None = None):
    factory = RepositoryFactory.create()
    try:
        records = factory.feed_rations().get_all()
        if animal_group:
            records = [r for r in records if r.animal_group == animal_group]
        return [
            {
                "id": r.id,
                "name": r.name,
                "animal_group": r.animal_group,
                "ingredients": json.loads(r.ingredients_json),
                "target_dmi_kg": r.target_dmi_kg,
                "dry_matter_pct": r.dry_matter_pct,
                "crude_protein_pct": r.crude_protein_pct,
                "ndf_pct": r.ndf_pct,
                "energy_mcal_kg": r.energy_mcal_kg,
                "cost_per_kg": r.cost_per_kg,
                "effective_date": r.effective_date,
                "operator": r.operator,
            }
            for r in records
        ]
    finally:
        factory.close()


@router.post("/records")
def record_feed(payload: FeedEntry):
    if not payload.animal_id and not payload.group_or_pen:
        raise HTTPException(status_code=400, detail="animal_id or group_or_pen is required")
    if payload.animal_id:
        factory = RepositoryFactory.create()
        try:
            if not factory.animal().exists(payload.animal_id):
                raise HTTPException(status_code=422, detail="Unknown Animal ID")
        finally:
            factory.close()
    factory = RepositoryFactory.create()
    try:
        record = FeedRecord(
            animal_id=payload.animal_id,
            group_or_pen=payload.group_or_pen,
            feed_type=payload.feed_type,
            quantity_kg=payload.quantity_kg,
            feeding_date=payload.feeding_date or utcnow(),
            notes=payload.notes,
            status="RECORDED",
        )
        saved = factory.feed().add(record)
        return {
            "id": saved.id,
            "animal_id": saved.animal_id,
            "group_or_pen": saved.group_or_pen,
            "feed_type": saved.feed_type,
            "quantity_kg": saved.quantity_kg,
            "feeding_date": saved.feeding_date,
            "status": saved.status,
            "data_status": "LIVE_PERSISTED_DATA",
        }
    finally:
        factory.close()


@router.get("/records")
def list_feed_records():
    factory = RepositoryFactory.create()
    try:
        return [
            {
                "id": r.id,
                "animal_id": r.animal_id,
                "group_or_pen": r.group_or_pen,
                "feed_type": r.feed_type,
                "quantity_kg": r.quantity_kg,
                "feeding_date": r.feeding_date,
                "status": r.status,
                "notes": r.notes,
            }
            for r in factory.feed().get_all()
        ]
    finally:
        factory.close()


@router.get("/overview")
def feed_overview():
    factory = RepositoryFactory.create()
    try:
        records = factory.feed().get_all()
        rations = factory.feed_rations().get_all()
        total_quantity = sum(float(r.quantity_kg or 0) for r in records)
        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "feeding_records": len(records),
            "ration_count": len(rations),
            "total_recorded_feed_kg": total_quantity,
            "nutrition_metrics": {
                "dry_matter_intake_kg": None,
                "crude_protein_pct": None,
                "ndf_pct": None,
                "energy_mcal_kg": None,
            },
            "interpretation": "Nutrition metrics are reported only when supported by persisted ration/measurement data; no synthetic values are generated.",
        }
    finally:
        factory.close()
