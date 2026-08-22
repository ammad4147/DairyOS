from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.api.reference_data import GOVERNED
from dairyos.data.models.feed_inventory_item import FeedInventoryItem
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.data.repositories.repository_factory import RepositoryFactory

router = APIRouter(prefix="/farm/feed-inventory", tags=["feed-inventory"])


class FeedInventoryItemEntry(BaseModel):
    item: str = Field(min_length=1)
    category: str = "FEED"
    unit: str = Field(default="kg", min_length=1)
    location: str | None = None
    reorder_level: float = Field(default=0, ge=0)
    active: bool = True
    notes: str | None = None


class FeedInventoryMovement(BaseModel):
    item: str = Field(min_length=1)
    quantity: float
    movement_type: str
    unit: str | None = None
    location: str | None = None
    supplier: str | None = None
    notes: str | None = None
    source_financial_transaction_id: int | None = Field(default=None, gt=0)


def _catalog_row(row: FeedInventoryItem) -> dict:
    return {
        "id": row.id,
        "item": row.item,
        "category": row.category,
        "unit": row.unit,
        "location": row.location,
        "reorder_level": float(row.reorder_level or 0),
        "active": bool(row.active),
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _movement_row(row: InventoryTransaction) -> dict:
    return {
        "id": row.id,
        "item": row.item,
        "movement_type": row.movement_type,
        "quantity": float(row.quantity or 0),
        "signed_quantity": float(row.signed_quantity or 0),
        "unit": row.unit,
        "location": row.location,
        "supplier": row.supplier,
        "notes": row.notes,
        "recorded_by": row.recorded_by,
        "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
    }


@router.get("/items")
def list_feed_inventory_items(active_only: bool = True):
    factory = RepositoryFactory.create()
    try:
        rows = factory.feed_inventory_items().get_all()
        if active_only:
            rows = [row for row in rows if row.active]
        return {"data_status": "LIVE_PERSISTED_DATA", "items": [_catalog_row(row) for row in rows]}
    finally:
        factory.close()


@router.post("/items")
def create_feed_inventory_item(payload: FeedInventoryItemEntry):
    item = payload.item.strip()
    factory = RepositoryFactory.create()
    try:
        if factory.feed_inventory_items().get_by_item(item) is not None:
            raise HTTPException(status_code=409, detail=f"Inventory item '{item}' already exists.")
        row = FeedInventoryItem(
            item=item,
            category=payload.category.strip().upper() or "FEED",
            unit=payload.unit.strip(),
            location=payload.location,
            reorder_level=payload.reorder_level,
            active=payload.active,
            notes=payload.notes,
        )
        saved = factory.feed_inventory_items().add(row)
        return _catalog_row(saved)
    finally:
        factory.close()


@router.patch("/items/{item_id}")
def edit_feed_inventory_item(item_id: int, payload: FeedInventoryItemEntry):
    factory = RepositoryFactory.create()
    try:
        row = factory.feed_inventory_items().get_by_id(item_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Feed inventory item not found.")
        existing = factory.feed_inventory_items().get_by_item(payload.item.strip())
        if existing is not None and existing.id != item_id:
            raise HTTPException(status_code=409, detail=f"Inventory item '{payload.item.strip()}' already exists.")
        row.item = payload.item.strip()
        row.category = payload.category.strip().upper() or "FEED"
        row.unit = payload.unit.strip()
        row.location = payload.location
        row.reorder_level = payload.reorder_level
        row.active = payload.active
        row.notes = payload.notes
        saved = factory.feed_inventory_items().add(row)
        return _catalog_row(saved)
    finally:
        factory.close()


@router.get("/movements")
def list_feed_inventory_movements(item: str | None = None, limit: int = Query(default=100, ge=1, le=500)):
    factory = RepositoryFactory.create()
    try:
        rows = factory.inventory().get_all()
        if item:
            rows = [row for row in rows if row.item == item]
        rows = sorted(rows, key=lambda row: row.recorded_at or datetime.min, reverse=True)[:limit]
        return {"data_status": "LIVE_PERSISTED_DATA", "movements": [_movement_row(row) for row in rows]}
    finally:
        factory.close()


@router.post("/movements")
def create_feed_inventory_movement(payload: FeedInventoryMovement):
    movement_type = payload.movement_type.strip().upper()
    allowed = set(GOVERNED["inventory_movement_types"])
    if movement_type not in allowed:
        raise HTTPException(status_code=422, detail=f"movement_type must be one of: {', '.join(sorted(allowed))}")

    factory = RepositoryFactory.create()
    try:
        catalog = factory.feed_inventory_items().get_by_item(payload.item.strip())
        if catalog is None or not catalog.active:
            raise HTTPException(status_code=422, detail="Select an active Feed Inventory Item from the catalog.")

        quantity = float(payload.quantity)
        if movement_type in {"TRANSFER", "ADJUSTMENT"}:
            if quantity == 0:
                raise HTTPException(status_code=422, detail=f"{movement_type} requires a nonzero quantity.")
            signed = quantity
            display_quantity = abs(quantity)
        else:
            if quantity <= 0:
                raise HTTPException(status_code=422, detail=f"{movement_type} requires a positive quantity.")
            signed = quantity if movement_type in {"PURCHASE", "RECEIPT"} else -quantity
            display_quantity = quantity

        unit = payload.unit or catalog.unit
        if unit != catalog.unit:
            raise HTTPException(status_code=422, detail=f"Unit mismatch: '{catalog.item}' is controlled as {catalog.unit}.")

        balance = factory.inventory().balance_by_item().get(catalog.item, {}).get("balance", 0.0)
        if signed < 0 and float(balance) + signed < 0:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "INSUFFICIENT_STOCK",
                    "item": catalog.item,
                    "available": float(balance),
                    "requested": display_quantity,
                    "unit": catalog.unit,
                },
            )

        if payload.source_financial_transaction_id is not None:
            finance_row = factory.finance().get_by_id(payload.source_financial_transaction_id)
            if finance_row is None:
                raise HTTPException(status_code=422, detail="source_financial_transaction_id not found.")

        transaction = InventoryTransaction(
            item=catalog.item,
            movement_type=movement_type,
            quantity=display_quantity,
            signed_quantity=signed,
            unit=unit,
            location=payload.location or catalog.location,
            supplier=payload.supplier,
            notes=(
                f"Finance transaction #{payload.source_financial_transaction_id}. {payload.notes or ''}".strip()
                if payload.source_financial_transaction_id is not None
                else payload.notes
            ),
        )
        saved = factory.inventory().add(transaction)
        return _movement_row(saved)
    finally:
        factory.close()


@router.get("/dashboard")
def feed_inventory_dashboard():
    factory = RepositoryFactory.create()
    try:
        catalog = [row for row in factory.feed_inventory_items().get_all() if row.active]
        balances = factory.inventory().balance_by_item()
        items = []
        low_stock = []
        for row in catalog:
            balance = float(balances.get(row.item, {}).get("balance", 0.0))
            threshold = float(row.reorder_level or 0.0)
            status = "NO_THRESHOLD" if threshold <= 0 else ("LOW" if balance <= threshold else "OK")
            record = {
                **_catalog_row(row),
                "balance": balance,
                "status": status,
                "transaction_count": balances.get(row.item, {}).get("transaction_count", 0),
                "last_movement_at": balances.get(row.item, {}).get("last_movement_at"),
            }
            items.append(record)
            if status == "LOW":
                low_stock.append(record)

        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "items": items,
            "low_stock": low_stock,
            "summary": {
                "active_items": len(items),
                "low_stock_items": len(low_stock),
                "tracked_without_threshold": sum(1 for row in items if row["status"] == "NO_THRESHOLD"),
            },
        }
    finally:
        factory.close()
