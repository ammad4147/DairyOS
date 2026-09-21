"""Row-level period OPEX attribution for the Finance -> OPEX -> COML trace.

``GET /farm/coml/integrated`` is the Estimated COP authority and computes the
period OPEX *total* inside its route handler, where a body of governance
tests pins it. Management Reporting needs the same decision *per Finance
transaction* so an auditor can see which rows produced that total.

This module applies the identical rules row by row, and delegates every
attribution decision to the same authority the COP endpoint uses
(``finance.opex_attribution.attributed_amount``). Reporting never trusts
this module on its own: the OPEX Reconciliation report calls the COP
authority as well and publishes the difference, which must be PKR 0.00, and
``tests/reporting`` asserts the equivalence on synthetic data.

Rules:

* VOID rows and non-expense rows never contribute.
* Only ``OPEX`` and ``NON_OPEX`` master categories are considered.
  ``FEED`` cost is governed by the TMR authority, not by Finance purchases.
* ``attributed_amount`` decides DIRECT / PERIODIC / ALLOCATED attribution
  against the inclusive period.
* A CONSUMPTION-method Semen Straw purchase is attributed by the straws
  drawn from its linked semen lot inside the period, at the lot unit cost.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from dairyos.data.models.semen_inventory import SemenLot, SemenStockMovement
from dairyos.finance.classification.transaction_classifier import is_expense
from dairyos.finance.opex_attribution import attributed_amount
from dairyos.finance.expense_measurement import measurement_policy
from dairyos.data.models.inventory_transaction import InventoryTransaction

SEMEN_PURCHASE_ITEM = "Semen Straws (Sexed / Conventional)"


@dataclass(frozen=True)
class OpexAttributionRow:
    transaction: Any
    amount: Decimal
    attributed: Decimal
    status: str  # ATTRIBUTED | OUTSIDE_PERIOD | UNATTRIBUTED | NON_OPEX


@dataclass
class OpexPeriodAttribution:
    start: date
    end: date
    rows: list[OpexAttributionRow] = field(default_factory=list)

    @property
    def opex_total(self) -> float:
        return sum(float(r.attributed) for r in self.rows if r.status == "ATTRIBUTED")

    @property
    def opex_total_decimal(self) -> Decimal:
        return sum(
            (r.attributed for r in self.rows if r.status == "ATTRIBUTED"),
            Decimal("0.00"),
        )

    @property
    def unattributed_total(self) -> float:
        return sum(float(r.amount) for r in self.rows if r.status == "UNATTRIBUTED")

    @property
    def unattributed_count(self) -> int:
        return sum(1 for r in self.rows if r.status == "UNATTRIBUTED")

    @property
    def non_opex_excluded_total(self) -> float:
        return sum(float(r.amount) for r in self.rows if r.status == "NON_OPEX")


def _semen_consumption(factory, item, start: date, end: date) -> Decimal | None:
    lot = (
        factory.session.query(SemenLot)
        .filter(SemenLot.purchase_transaction_id == item.id)
        .first()
    )
    if lot is None:
        return None
    movements = (
        factory.session.query(SemenStockMovement)
        .filter(
            SemenStockMovement.semen_lot_id == lot.id,
            SemenStockMovement.signed_quantity < 0,
        )
        .all()
    )
    used_quantity = sum(
        abs(int(movement.signed_quantity or 0))
        for movement in movements
        if (
            getattr(movement, "recorded_at", None) is not None
            and start <= movement.recorded_at.date() <= end
        )
    )
    if used_quantity <= 0:
        return None
    return (Decimal(str(lot.unit_cost)) * Decimal(used_quantity)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _clinical_consumption(factory, item, start: date, end: date) -> Decimal | None:
    """Recognize only operator-recorded clinical stock consumed from this purchase."""
    policy = measurement_policy(getattr(item, "sub_category", None))
    if policy.quantity_kind != "purchase":
        return None
    receipts = factory.session.query(InventoryTransaction).filter(
        InventoryTransaction.source_type == "CLINICAL_RECEIPT",
        InventoryTransaction.source_id == str(item.id),
        InventoryTransaction.item == getattr(item, "sub_category", None),
    ).all()
    if not receipts:
        return None
    receipt_qty = sum(Decimal(str(row.quantity or 0)) for row in receipts)
    if receipt_qty <= 0:
        return None
    consumed = factory.session.query(InventoryTransaction).filter(
        InventoryTransaction.item == getattr(item, "sub_category", None),
        InventoryTransaction.source_type.in_(["TREATMENT_CONSUMPTION", "VACCINATION_CONSUMPTION"]),
        InventoryTransaction.signed_quantity < 0,
    ).all()
    used = sum(
        abs(Decimal(str(row.signed_quantity or 0)))
        for row in consumed
        if getattr(row, "recorded_at", None) is not None and start <= row.recorded_at.date() <= end
    )
    if used <= 0:
        return None
    return (Decimal(str(item.amount)) * used / receipt_qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def attribute_opex_for_period(
    factory,
    start: date,
    end: date,
    *,
    transactions: list[Any] | None = None,
) -> OpexPeriodAttribution:
    """Attribute every active Finance OPEX / NON_OPEX expense to ``[start, end]``."""
    result = OpexPeriodAttribution(start=start, end=end)
    source = transactions if transactions is not None else (factory.finance().get_all() or [])

    for item in source:
        status = str(getattr(item, "status", "RECORDED") or "RECORDED").strip().upper()
        if status == "VOID" or not is_expense(item):
            continue

        master = str(getattr(item, "master_category", "") or "").strip().upper()
        # Both governed NON_OPEX rows and historical OPEX rows carrying a
        # persisted NON_OPEX classification reach the shared attribution
        # authority. FEED remains governed by TMR.
        if master not in {"OPEX", "NON_OPEX"}:
            continue

        amount = float(getattr(item, "amount", 0.0) or 0.0)
        if amount <= 0:
            continue

        attributed, attribution_status = attributed_amount(item, start, end)

        if (
            attribution_status == "UNATTRIBUTED"
            and str(getattr(item, "cop_attribution_method", "") or "").upper() == "CONSUMPTION"
            and str(getattr(item, "sub_category", "") or "").strip() == SEMEN_PURCHASE_ITEM
        ):
            consumed = _semen_consumption(factory, item, start, end)
            if consumed is not None:
                attributed = consumed
                attribution_status = "ATTRIBUTED"

        if (
            attribution_status == "UNATTRIBUTED"
            and str(getattr(item, "cop_attribution_method", "") or "").upper() == "CONSUMPTION"
        ):
            consumed = _clinical_consumption(factory, item, start, end)
            if consumed is not None:
                attributed = consumed
                attribution_status = "ATTRIBUTED"

        result.rows.append(
            OpexAttributionRow(
                transaction=item,
                amount=Decimal(str(getattr(item, "amount", 0) or 0)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                attributed=Decimal(str(attributed)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                status=attribution_status,
            )
        )

    return result
