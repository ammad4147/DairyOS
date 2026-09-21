"""Operator-controlled inventory movements for clinical consumables.

Clinical events never infer stock usage from a free-form dose.  A movement is
created only when the operator supplies an inventory item, quantity, and unit.
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException

from dairyos.data.models.inventory_transaction import InventoryTransaction
from dairyos.finance.expense_measurement import allowed_units


def record_clinical_consumption(
    container,
    *,
    item: str,
    quantity: float,
    unit: str,
    source_type: str,
    source_id: str | int,
    recorded_by: str,
    notes: str | None = None,
) -> InventoryTransaction:
    """Consume an explicitly selected clinical inventory item exactly once."""
    item = str(item or "").strip()
    unit = str(unit or "").strip()
    if not item or not unit or quantity <= 0:
        raise HTTPException(status_code=422, detail="Clinical consumption requires item, positive quantity, and unit.")
    if unit not in set(allowed_units(item)) and unit not in {"dose", "vial", "mL", "L", "tablet", "tube", "piece", "pack", "box"}:
        raise HTTPException(status_code=422, detail=f"Unit {unit!r} is not governed for clinical inventory item {item!r}.")

    repo = container.repository_factory.inventory()
    existing = next(
        (row for row in repo.get_all() if row.source_type == source_type and str(row.source_id) == str(source_id)),
        None,
    )
    if existing is not None:
        return existing

    balance = Decimal(0)
    for row in repo.get_all():
        if row.item != item:
            continue
        if str(row.unit or "") != unit:
            raise HTTPException(status_code=409, detail=f"Inventory item {item!r} has incompatible units; reconcile stock before consuming it.")
        balance += Decimal(str(row.signed_quantity or 0))
    if balance < Decimal(str(quantity)):
        raise HTTPException(status_code=409, detail=f"Insufficient stock for {item!r}: {balance} {unit} available, {quantity} {unit} requested.")

    movement = InventoryTransaction(
        item=item,
        movement_type="CONSUMPTION",
        quantity=float(quantity),
        signed_quantity=-float(quantity),
        unit=unit,
        notes=notes,
        recorded_by=recorded_by,
        source_type=source_type,
        source_id=str(source_id),
    )
    return repo.add(movement)


def record_clinical_receipt(
    container,
    *,
    item: str,
    quantity: float,
    unit: str,
    recorded_by: str,
    supplier: str | None = None,
    source_id: str | None = None,
    notes: str | None = None,
) -> InventoryTransaction:
    """Record operator-confirmed receipt; purchase accounting stays in Finance."""
    if quantity <= 0 or not item or not unit:
        raise HTTPException(status_code=422, detail="Clinical receipt requires item, positive quantity, and unit.")
    if unit not in set(allowed_units(item)) and unit not in {"dose", "vial", "mL", "L", "tablet", "tube", "piece", "pack", "box"}:
        raise HTTPException(status_code=422, detail=f"Unit {unit!r} is not governed for clinical inventory item {item!r}.")
    return container.repository_factory.inventory().add(InventoryTransaction(
        item=str(item).strip(), movement_type="RECEIPT", quantity=float(quantity),
        signed_quantity=float(quantity), unit=str(unit).strip(), supplier=supplier,
        notes=notes, recorded_by=recorded_by, source_type="CLINICAL_RECEIPT",
        source_id=source_id,
    ))
