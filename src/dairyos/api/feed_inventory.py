from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.api.dependencies import get_container
from dairyos.api.reference_data import GOVERNED
from dairyos.data.models.feed_inventory_item import FeedInventoryItem
from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.finance.classification.transaction_classifier import is_active

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
    recorded_by: str | None = None
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
        "source_type": getattr(row, "source_type", None),
        "source_id": getattr(row, "source_id", None),
        "source_financial_transaction_id": getattr(row, "source_financial_transaction_id", None),
    }



def _finance_feed_item_name(row):
    if str(row.master_category or "").strip().upper() != "FEED":
        return None

    sub = str(row.sub_category or "").strip()

    if not sub:
        return None

    if sub == "Other":
        custom = str(
            getattr(row, "custom_specification", None) or ""
        ).strip()
        return custom or None

    return sub

def _finance_purchase_rows(factory, item: str):
    rows = factory.finance().get_all()
    return [
        row
        for row in rows
        if is_active(row)
        and str(row.transaction_type or "").upper() in {"EXPENSE", "PAYMENT", "PURCHASE"}
        and str(row.master_category or "").upper() == "FEED"
        and _finance_feed_item_name(row) == item
        and float(row.quantity or 0) > 0
    ]



def _latest_finance_purchase(
    factory,
    item: str,
    unit: str | None = None,
):
    rows = []

    for row in _finance_purchase_rows(factory, item):
        row_unit = str(row.unit or unit or "").strip()

        if unit and row_unit != unit:
            continue

        if float(row.unit_rate or 0) <= 0:
            continue

        rows.append(row)

    if not rows:
        return None

    return max(
        rows,
        key=lambda row: (
            row.transaction_date or datetime.min,
            int(row.id or 0),
        ),
    )


def _latest_finance_unit_rate(
    factory,
    item: str,
    unit: str | None = None,
) -> float | None:
    row = _latest_finance_purchase(
        factory,
        item,
        unit,
    )

    if row is None:
        return None

    return float(row.unit_rate or 0)

def _finance_purchased_quantity(factory, item: str, unit: str | None = None) -> float:
    total = 0.0
    for row in _finance_purchase_rows(factory, item):
        row_unit = str(row.unit or unit or "").strip()
        if unit and row_unit != unit:
            continue
        total += float(row.quantity or 0)
    return total


def _operational_balance(factory, item: str) -> float:
    rows = factory.inventory().get_all()
    balance = 0.0
    for row in rows:
        if row.item != item:
            continue
        movement_type = str(row.movement_type or "").upper()
        notes = str(row.notes or "")
        if movement_type in {"PURCHASE", "RECEIPT"} and notes.startswith("Finance transaction #"):
            continue
        balance += float(row.signed_quantity or 0)
    return balance


def _feed_raw_balance(factory, item: str, unit: str | None = None) -> float:
    purchased = _finance_purchased_quantity(factory, item, unit)
    operational = _operational_balance(factory, item)
    return purchased + operational


def _feed_balance(factory, item: str, unit: str | None = None) -> float:
    return max(0.0, _feed_raw_balance(factory, item, unit))


def _factory(container):
    factory = getattr(container, "repository_factory", None)
    if factory is None:
        raise HTTPException(status_code=503, detail="Canonical repository factory is not available")
    return factory


@router.get("/items")
def list_feed_inventory_items(active_only: bool = True, container=Depends(get_container)):
    factory = _factory(container)
    rows = factory.feed_inventory_items().get_all()
    if active_only:
        rows = [row for row in rows if row.active]
    return {"data_status": "LIVE_PERSISTED_DATA", "items": [_catalog_row(row) for row in rows]}


@router.post("/items")
def create_feed_inventory_item(payload: FeedInventoryItemEntry, container=Depends(get_container)):
    item = payload.item.strip()
    factory = _factory(container)
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
    return _catalog_row(factory.feed_inventory_items().add(row))


@router.patch("/items/{item_id}")
def edit_feed_inventory_item(item_id: int, payload: FeedInventoryItemEntry, container=Depends(get_container)):
    factory = _factory(container)
    repository = factory.feed_inventory_items()
    row = repository.get_by_id(item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Feed inventory item not found.")
    existing = repository.get_by_item(payload.item.strip())
    if existing is not None and existing.id != item_id:
        raise HTTPException(status_code=409, detail=f"Inventory item '{payload.item.strip()}' already exists.")
    row.item = payload.item.strip()
    row.category = payload.category.strip().upper() or "FEED"
    row.unit = payload.unit.strip()
    row.location = payload.location
    row.reorder_level = payload.reorder_level
    row.active = payload.active
    row.notes = payload.notes
    return _catalog_row(repository.add(row))


@router.get("/movements")
def list_feed_inventory_movements(
    item: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    container=Depends(get_container),
):
    factory = _factory(container)
    rows = factory.inventory().get_all()
    if item:
        rows = [row for row in rows if row.item == item]
    rows = sorted(rows, key=lambda row: row.recorded_at or datetime.min, reverse=True)[:limit]
    return {"data_status": "LIVE_PERSISTED_DATA", "movements": [_movement_row(row) for row in rows]}


@router.post("/movements")
def create_feed_inventory_movement(payload: FeedInventoryMovement, container=Depends(get_container)):
    movement_type = payload.movement_type.strip().upper()

    if movement_type in {"CONSUMPTION", "WASTAGE"}:
        raise HTTPException(
            status_code=410,
            detail=(
                "Direct Record Feed Usage is retired. "
                "Feed consumption is governed automatically by TMR. "
                "Use Feed Storage manual override only for physical stock corrections."
            ),
        )

    allowed = set(GOVERNED["inventory_movement_types"])
    if movement_type not in allowed:
        raise HTTPException(status_code=422, detail="movement_type must be one of: " + ", ".join(sorted(allowed)))

    factory = _factory(container)
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

    available = _feed_balance(factory, catalog.item, catalog.unit)
    if signed < 0 and available + signed < 0:
        raise HTTPException(
            status_code=409,
            detail={"error": "INSUFFICIENT_STOCK", "item": catalog.item, "available": available, "requested": display_quantity, "unit": catalog.unit},
        )

    if payload.source_financial_transaction_id is not None:
        finance_row = factory.finance().get_by_id(payload.source_financial_transaction_id)
        if finance_row is None:
            raise HTTPException(status_code=422, detail="source_financial_transaction_id not found.")
        if (
            not is_active(finance_row)
            or str(finance_row.transaction_type or "").upper() not in {"EXPENSE", "PAYMENT", "PURCHASE"}
            or str(finance_row.master_category or "").upper() != "FEED"
        ):
            raise HTTPException(status_code=422, detail="source_financial_transaction_id must reference an active Finance Feed expense.")

    transaction = InventoryTransaction(
        item=catalog.item,
        movement_type=movement_type,
        quantity=display_quantity,
        signed_quantity=signed,
        unit=unit,
        location=payload.location or catalog.location,
        supplier=payload.supplier,
        notes=((f"Finance transaction #{payload.source_financial_transaction_id}. {payload.notes or ''}").strip() if payload.source_financial_transaction_id is not None else payload.notes),
        recorded_by=payload.recorded_by or "WEB",
    )
    return _movement_row(factory.inventory().add(transaction))


@router.get("/dashboard")
def feed_inventory_dashboard(container=Depends(get_container)):
    factory = _factory(container)
    catalog = [row for row in factory.feed_inventory_items().get_all() if row.active]
    items = []
    low_stock = []
    for row in catalog:
        raw_balance = _feed_raw_balance(factory, row.item, row.unit)
        balance = max(0.0, raw_balance)
        shortage = max(0.0, -raw_balance)
        threshold = float(row.reorder_level or 0.0)
        status = (
            "SHORTAGE"
            if shortage > 0
            else (
                "NO_THRESHOLD"
                if threshold <= 0
                else ("LOW" if balance <= threshold else "OK")
            )
        )
        movement_rows = [movement for movement in factory.inventory().get_all() if movement.item == row.item]
        movement_breakdown = _storage_movement_breakdown(movement_rows)
        record = {
            **_catalog_row(row),
            "balance": balance,
            "projected_balance": round(raw_balance, 3),
            "shortage": round(shortage, 3),
            "purchased_from_finance": _finance_purchased_quantity(factory, row.item, row.unit),
            "auto_consumed_from_tmr": movement_breakdown["auto_consumed_from_tmr"],
            "manual_override_net": movement_breakdown["manual_override_net"],
            "legacy_manual_usage": movement_breakdown["legacy_manual_usage"],
            "latest_finance_unit_rate": _latest_finance_unit_rate(factory, row.item, row.unit),
            "status": status,
            "transaction_count": len(movement_rows),
            "last_movement_at": max((movement.recorded_at for movement in movement_rows if movement.recorded_at), default=None),
        }
        items.append(record)
        if status == "LOW":
            low_stock.append(record)
    return {
        "data_status": "LIVE_PERSISTED_DATA",
        "items": items,
        "low_stock": low_stock,
        "item_count": len(items),
        "low_stock_count": len(low_stock),
        "summary": {
            "active_items": len(items),
            "low_stock_items": len(low_stock),
            "tracked_without_threshold": sum(1 for row in items if row["status"] == "NO_THRESHOLD"),
        },
    }


# ---------------------------------------------------------------------
# Governed TMR -> Feed Storage authority
# ---------------------------------------------------------------------

TMR_AUTO_CONSUMPTION_MARKER = "TMR_AUTO_CONSUMPTION_DATE="
FEED_STORAGE_OVERRIDE_MARKER = "FEED_STORAGE_MANUAL_OVERRIDE"


class FeedStorageManualOverride(BaseModel):
    item: str
    quantity_delta: float
    notes: str | None = None
    recorded_by: str = "WEB"


def _auto_consumption_date(notes: str | None) -> str | None:
    text = str(notes or "")
    position = text.find(TMR_AUTO_CONSUMPTION_MARKER)

    if position < 0:
        return None

    start = position + len(TMR_AUTO_CONSUMPTION_MARKER)
    value = text[start:start + 10]

    if len(value) == 10 and value[4] == "-" and value[7] == "-":
        return value

    return None


def _storage_movement_breakdown(movements) -> dict:
    auto_consumed = 0.0
    manual_override = 0.0
    legacy_usage = 0.0

    for movement in movements:
        signed = float(getattr(movement, "signed_quantity", 0.0) or 0.0)
        movement_type = str(
            getattr(movement, "movement_type", "") or ""
        ).upper()
        notes = str(getattr(movement, "notes", "") or "")

        if TMR_AUTO_CONSUMPTION_MARKER in notes:
            if signed < 0:
                auto_consumed += abs(signed)
            continue

        if FEED_STORAGE_OVERRIDE_MARKER in notes:
            manual_override += signed
            continue

        if movement_type in {"CONSUMPTION", "WASTAGE"} and signed < 0:
            legacy_usage += abs(signed)

    return {
        "auto_consumed_from_tmr": round(auto_consumed, 3),
        "manual_override_net": round(manual_override, 3),
        "legacy_manual_usage": round(legacy_usage, 3),
    }


def _tmr_ingredient_requirement(summary: dict) -> dict[str, float]:
    """
    Convert governed TMR category rations into whole-herd kg/day demand.

    Milking and Dry use the arithmetic mean of their governed stage rations,
    exactly matching DairyOS category cost authority.
    """
    stages = summary.get("stages") or {}
    categories = summary.get("categories") or []

    demand: dict[str, float] = {}

    for category in categories:
        animal_count = int(category.get("animal_count") or 0)

        if animal_count <= 0:
            continue

        stage_keys = list(category.get("stage_keys") or [])

        if not stage_keys:
            continue

        names: set[str] = set()

        for stage_key in stage_keys:
            stage = stages.get(stage_key) or {}

            for ingredient in stage.get("ingredients") or []:
                name = str(ingredient.get("catalog_name") or "").strip()

                if name:
                    names.add(name)

        for name in names:
            stage_values: list[float] = []

            for stage_key in stage_keys:
                stage = stages.get(stage_key) or {}
                ingredient_row = next(
                    (
                        row
                        for row in stage.get("ingredients") or []
                        if str(row.get("catalog_name") or "").strip() == name
                    ),
                    None,
                )

                if ingredient_row is None:
                    stage_values.append(0.0)
                    continue

                quantity = float(ingredient_row.get("quantity") or 0.0)
                dose_unit = str(
                    ingredient_row.get("dose_unit") or "kg"
                ).strip().lower()

                quantity_kg = (
                    quantity / 1000.0
                    if dose_unit == "g"
                    else quantity
                )

                stage_values.append(quantity_kg)

            average_per_head = (
                sum(stage_values) / len(stage_keys)
                if stage_keys
                else 0.0
            )

            demand[name] = (
                demand.get(name, 0.0)
                + average_per_head * animal_count
            )

    return {
        name: round(quantity, 6)
        for name, quantity in demand.items()
        if quantity > 0
    }


def _ensure_tmr_storage_catalog(factory, summary: dict) -> None:
    definitions = summary.get("ingredients") or []
    repository = factory.feed_inventory_items()

    for definition in definitions:
        name = str(definition.get("catalog_name") or "").strip()

        if not name:
            continue

        existing = repository.get_by_item(name)

        if existing is None:
            row = FeedInventoryItem(
                item=name,
                category="FEED",
                unit="kg",
                reorder_level=0,
                active=True,
                notes=(
                    "Established automatically from governed "
                    "TMR Feed Storage authority."
                ),
            )
            factory.session.add(row)
            continue

        changed = False

        if not bool(getattr(existing, "active", True)):
            existing.active = True
            changed = True

        if not str(getattr(existing, "unit", "") or "").strip():
            existing.unit = "kg"
            changed = True

        if changed:
            factory.session.add(existing)

    factory.session.flush()


def _storage_summary_for_day(factory, day, today, live_summary: dict):
    """
    Historical priority:
    1. Existing daily auto movement is never rewritten after that day closes.
    2. For an unsynchronised past day, use weekly Vet-endorsed TMR when present.
    3. Otherwise use the live TMR as an explicit fallback.
    """
    if day == today:
        return live_summary, "LIVE_TMR"

    from dairyos.api.tmr import _endorsement_snapshots, _week_bounds

    week_start, _ = _week_bounds(day)

    for snapshot in _endorsement_snapshots(factory):
        if str(snapshot.get("week_start") or "") == week_start.isoformat():
            return snapshot, "WEEKLY_VET_ENDORSED_TMR"

    return live_summary, "UNENDORSED_LIVE_TMR_FALLBACK"


def reconcile_tmr_feed_storage(factory):
    """
    Idempotently materialise governed TMR consumption into Feed Storage.

    The first sync establishes the cutover date implicitly. Future syncs
    continue from the earliest TMR auto-consumption date. Closed historical
    dates with existing materialised rows are not recalculated.
    """
    from datetime import date, timedelta
    from dairyos.api.tmr import build_live_tmr_summary

    live_summary = build_live_tmr_summary(
        factory,
        include_weekly_review=False,
    )

    today = date.fromisoformat(
        str(live_summary["operational_date"])
    )

    _ensure_tmr_storage_catalog(factory, live_summary)

    movements = list(factory.inventory().get_all())

    auto_dates = [
        value
        for value in (
            _auto_consumption_date(
                getattr(movement, "notes", None)
            )
            for movement in movements
        )
        if value
    ]

    start = (
        date.fromisoformat(min(auto_dates))
        if auto_dates
        else today
    )

    created_rows = 0
    reconciled_rows = 0
    day_rows: list[dict] = []

    day = start

    while day <= today:
        day_iso = day.isoformat()

        existing_for_day = [
            movement
            for movement in movements
            if _auto_consumption_date(
                getattr(movement, "notes", None)
            ) == day_iso
        ]

        # Once a prior operational day has been materialised it is immutable.
        if day < today and existing_for_day:
            day_rows.append(
                {
                    "date": day_iso,
                    "basis": "LOCKED_DAILY_AUTO_TMR",
                    "status": "UNCHANGED",
                }
            )
            day += timedelta(days=1)
            continue

        summary, basis = _storage_summary_for_day(
            factory,
            day,
            today,
            live_summary,
        )

        requirement = _tmr_ingredient_requirement(summary)

        existing_items = {
            str(getattr(row, "item", "") or "")
            for row in existing_for_day
        }

        all_items = sorted(
            set(requirement) | existing_items
        )

        for item in all_items:
            catalog = factory.feed_inventory_items().get_by_item(item)

            if catalog is None:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "TMR Feed Storage catalog authority "
                        f"is missing for '{item}'."
                    ),
                )

            item_movements = [
                movement
                for movement in movements
                if str(getattr(movement, "item", "") or "") == item
            ]

            has_finance_stock_authority = (
                _finance_purchased_quantity(
                    factory,
                    item,
                    catalog.unit,
                ) > 0
            )

            has_positive_manual_stock_authority = any(
                FEED_STORAGE_OVERRIDE_MARKER
                in str(getattr(movement, "notes", "") or "")
                and float(
                    getattr(movement, "signed_quantity", 0.0)
                    or 0.0
                ) > 0
                for movement in item_movements
            )

            has_prior_auto_authority = any(
                TMR_AUTO_CONSUMPTION_MARKER
                in str(getattr(movement, "notes", "") or "")
                for movement in item_movements
            )

            has_storage_authority = (
                has_finance_stock_authority
                or has_positive_manual_stock_authority
                or has_prior_auto_authority
                or item in existing_items
            )

            # A TMR ingredient does not become negative historical stock
            # merely because it exists in the ration catalog. Automatic
            # consumption starts after Finance or a positive manual
            # physical-stock override establishes storage authority.
            if not has_storage_authority:
                continue

            target_consumption = float(
                requirement.get(item, 0.0)
            )
            target_signed = -target_consumption

            existing_signed = sum(
                float(
                    getattr(row, "signed_quantity", 0.0)
                    or 0.0
                )
                for row in existing_for_day
                if str(getattr(row, "item", "") or "") == item
            )

            delta = target_signed - existing_signed

            if abs(delta) <= 0.0005:
                continue

            transaction = InventoryTransaction(
                item=item,
                movement_type="ADJUSTMENT",
                quantity=abs(delta),
                signed_quantity=delta,
                unit=catalog.unit or "kg",
                location=catalog.location,
                supplier=None,
                notes=(
                    f"{TMR_AUTO_CONSUMPTION_MARKER}{day_iso}; "
                    f"BASIS={basis}; "
                    f"TARGET_DAILY_KG={target_consumption:.6f}"
                ),
                recorded_by="SYSTEM_TMR",
            )

            factory.session.add(transaction)

            if existing_signed == 0:
                created_rows += 1
            else:
                reconciled_rows += 1

        day_rows.append(
            {
                "date": day_iso,
                "basis": basis,
                "status": "SYNCHRONISED",
            }
        )

        day += timedelta(days=1)

    factory.session.commit()

    return {
        "data_status": "LIVE_PERSISTED_DATA",
        "source": "GOVERNED_TMR_X_ACTIVE_HERD",
        "cutover_date": start.isoformat(),
        "operational_date": today.isoformat(),
        "created_rows": created_rows,
        "reconciled_rows": reconciled_rows,
        "days": day_rows,
    }


@router.post("/automatic-consumption/sync")
def sync_tmr_feed_storage(container=Depends(get_container)):
    """Compatibility/API wrapper for governed TMR storage reconciliation."""
    return reconcile_tmr_feed_storage(
        _factory(container)
    )


@router.post("/manual-override")
def manual_feed_storage_override(
    payload: FeedStorageManualOverride,
    container=Depends(get_container),
):
    """
    Record a deliberate signed physical-stock correction.

    Positive quantity_delta adds stock.
    Negative quantity_delta removes stock.
    This is not a second feed-consumption workflow.
    """
    factory = _factory(container)

    item = payload.item.strip()
    delta = float(payload.quantity_delta)

    if not item:
        raise HTTPException(
            status_code=422,
            detail="item is required.",
        )

    if delta == 0:
        raise HTTPException(
            status_code=422,
            detail="quantity_delta must be nonzero.",
        )

    catalog = factory.feed_inventory_items().get_by_item(item)

    if catalog is None or not catalog.active:
        raise HTTPException(
            status_code=422,
            detail=(
                "Select an active Feed Storage item "
                "from the governed catalog."
            ),
        )

    current_raw = _feed_raw_balance(
        factory,
        catalog.item,
        catalog.unit,
    )

    if delta < 0 and current_raw + delta < 0:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "INSUFFICIENT_STOCK_FOR_OVERRIDE",
                "item": catalog.item,
                "projected_balance": round(current_raw, 3),
                "requested_delta": delta,
                "unit": catalog.unit,
            },
        )

    notes = (
        f"{FEED_STORAGE_OVERRIDE_MARKER}; "
        f"{payload.notes or ''}"
    ).strip()

    transaction = InventoryTransaction(
        item=catalog.item,
        movement_type="ADJUSTMENT",
        quantity=abs(delta),
        signed_quantity=delta,
        unit=catalog.unit,
        location=catalog.location,
        supplier=None,
        notes=notes,
        recorded_by=payload.recorded_by or "WEB",
    )

    saved = factory.inventory().add(transaction)

    return {
        "data_status": "LIVE_PERSISTED_DATA",
        "source": "MANUAL_PHYSICAL_STOCK_OVERRIDE",
        "movement": _movement_row(saved),
        "projected_balance": round(
            _feed_raw_balance(
                factory,
                catalog.item,
                catalog.unit,
            ),
            3,
        ),
    }
