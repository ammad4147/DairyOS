from __future__ import annotations

import json
from datetime import datetime, time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.data.models.feed_ration import FeedRation
from dairyos.data.models.feed_record import FeedRecord
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.core.time_utils import utcnow
from dairyos.farm.settings.services.operational_date_authority import (
    OperationalDateAuthority,
)
from dairyos.finance.classification.transaction_classifier import is_active

router = APIRouter(prefix="/farm/feed", tags=["feed-nutrition"])

INACTIVE_OPERATIONAL_STATUSES = frozenset({"VOID", "CANCELLED", "DELETED"})


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


def _inventory_balance(factory, item: str) -> float:
    return round(sum(float(row.signed_quantity or 0.0) for row in factory.inventory().get_all() if str(row.item).strip() == item), 3)


def _existing_feed_consumption(factory, feed_record_id: int):
    for row in factory.inventory().get_all():
        if str(getattr(row, "source_type", "") or "").upper() == "FEED_RECORD" and str(getattr(row, "source_id", "") or "") == str(feed_record_id):
            return row
    return None


def _feeding_day(value: datetime | None, factory) -> datetime:
    if value is not None:
        return value
    operational_date = OperationalDateAuthority(
        repository_factory=factory,
    ).current_date()
    return datetime.combine(operational_date, time.min)


def _historical_feed_cost(factory, feed_type: str, feeding_date: datetime):
    """Return the latest defensible persisted feed unit-cost basis at feeding time."""
    target = feeding_date.replace(tzinfo=None) if feeding_date.tzinfo else feeding_date
    candidates = []
    for row in factory.finance().get_all():
        if not is_active(row):
            continue
        if str(getattr(row, "transaction_type", "") or "").upper() not in {"EXPENSE", "PAYMENT", "PURCHASE"}:
            continue
        if str(getattr(row, "master_category", "") or "").upper() != "FEED":
            continue
        if str(getattr(row, "sub_category", "") or "").strip() != feed_type.strip():
            continue
        timestamp = getattr(row, "transaction_date", None)
        if timestamp is None:
            continue
        timestamp = timestamp.replace(tzinfo=None) if timestamp.tzinfo else timestamp
        if timestamp > target:
            continue
        unit = str(getattr(row, "unit", "") or "").strip().lower()
        if unit and unit not in {"kg", "kgs", "kilogram", "kilograms"}:
            continue
        unit_rate = getattr(row, "unit_rate", None)
        quantity = getattr(row, "quantity", None)
        if unit_rate is None and quantity:
            amount = float(getattr(row, "amount", 0.0) or 0.0)
            qty = float(quantity or 0.0)
            unit_rate = amount / qty if qty > 0 else None
        if unit_rate is None or float(unit_rate) <= 0:
            continue
        candidates.append((timestamp, float(unit_rate), getattr(row, "id", None)))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[2] or 0), reverse=True)
    _, unit_rate, source_id = candidates[0]
    return {
        "unit_cost_per_kg": unit_rate,
        "cost_basis": "FINANCE_FEED_PURCHASE",
        "cost_source_financial_transaction_id": source_id,
    }


@router.post("/records")
def record_feed(payload: FeedEntry):
    if not payload.animal_id and not payload.group_or_pen:
        raise HTTPException(status_code=400, detail="animal_id or group_or_pen is required")
    factory = RepositoryFactory.create()
    try:
        if payload.animal_id and not factory.animal().exists(payload.animal_id):
            raise HTTPException(status_code=422, detail="Unknown Animal ID")
        feeding_date = _feeding_day(payload.feeding_date, factory)
        cost = _historical_feed_cost(factory, payload.feed_type.strip(), feeding_date)
        quantity = float(payload.quantity_kg)
        unit_cost = cost["unit_cost_per_kg"] if cost else None
        record = FeedRecord(
            animal_id=payload.animal_id,
            group_or_pen=payload.group_or_pen,
            feed_type=payload.feed_type.strip(),
            quantity_kg=quantity,
            feeding_date=feeding_date,
            notes=payload.notes,
            status="RECORDED",
            unit_cost_per_kg=unit_cost,
            total_feed_cost=quantity * unit_cost if unit_cost is not None else None,
            cost_basis=cost["cost_basis"] if cost else "UNPRICED",
            cost_source_financial_transaction_id=cost["cost_source_financial_transaction_id"] if cost else None,
        )
        session = factory.session
        session.add(record)
        session.flush()
        if _existing_feed_consumption(factory, record.id) is None:
            session.add(InventoryTransaction(item=record.feed_type, movement_type="CONSUMPTION", quantity=quantity, signed_quantity=-quantity, unit="kg", notes=f"Auto-deducted from feeding record #{record.id}. {record.notes or ''}".strip(), recorded_by="FEED_API", source_type="FEED_RECORD", source_id=str(record.id), recorded_at=feeding_date))
        session.commit()
        session.refresh(record)
        inventory_balance = _inventory_balance(factory, record.feed_type)
        return {"id": record.id, "animal_id": record.animal_id, "group_or_pen": record.group_or_pen, "feed_type": record.feed_type, "quantity_kg": record.quantity_kg, "feeding_date": record.feeding_date, "status": record.status, "unit_cost_per_kg": record.unit_cost_per_kg, "total_feed_cost": record.total_feed_cost, "cost_basis": record.cost_basis, "cost_source_financial_transaction_id": record.cost_source_financial_transaction_id, "inventory_balance_kg": inventory_balance, "inventory_status": "NEGATIVE_STOCK_EXCEPTION" if inventory_balance < 0 else "BALANCED", "data_status": "LIVE_PERSISTED_DATA"}
    except HTTPException:
        factory.rollback()
        raise
    except Exception:
        factory.rollback()
        raise
    finally:
        factory.close()


@router.get("/records")
def list_feed_records():
    factory = RepositoryFactory.create()
    try:
        return [{"id": r.id, "animal_id": r.animal_id, "group_or_pen": r.group_or_pen, "feed_type": r.feed_type, "quantity_kg": r.quantity_kg, "feeding_date": r.feeding_date, "status": r.status, "notes": r.notes, "unit_cost_per_kg": getattr(r, "unit_cost_per_kg", None), "total_feed_cost": getattr(r, "total_feed_cost", None), "cost_basis": getattr(r, "cost_basis", None), "cost_source_financial_transaction_id": getattr(r, "cost_source_financial_transaction_id", None)} for r in factory.feed().get_all()]
    finally:
        factory.close()


@router.get("/overview")
def feed_overview():
    factory = RepositoryFactory.create()
    try:
        records = factory.feed().get_all()
        active_records = [
            r
            for r in records
            if str(getattr(r, "status", "RECORDED") or "RECORDED").upper()
            not in INACTIVE_OPERATIONAL_STATUSES
        ]
        rations = factory.feed_rations().get_all()
        priced = [r for r in active_records if getattr(r, "total_feed_cost", None) is not None]
        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "feeding_records": len(active_records),
            "historical_inactive_records": len(records) - len(active_records),
            "ration_count": len(rations),
            "total_recorded_feed_kg": sum(float(r.quantity_kg or 0) for r in active_records),
            "priced_feed_kg": sum(float(r.quantity_kg or 0) for r in priced),
            "priced_feed_cost": round(sum(float(r.total_feed_cost or 0) for r in priced), 2),
            "unpriced_feed_records": len(active_records) - len(priced),
            "nutrition_metrics": {
                "dry_matter_intake_kg": None,
                "crude_protein_pct": None,
                "ndf_pct": None,
                "energy_mcal_kg": None,
            },
            "interpretation": "Nutrition metrics are reported only when supported by persisted ration/measurement data; feed economics use historical persisted purchase prices when available and never invent missing costs. VOID/CANCELLED/DELETED records remain in history but are excluded from active totals.",
        }
    finally:
        factory.close()
