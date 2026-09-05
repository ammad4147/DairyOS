"""Persistent Finance ledger API.

Finance remains one unified ledger. Feed/OPEX are analytical dimensions on
expense rows; credit-control adds due/settlement dates and ageing without
creating a second ledger.

Milk Sales are additionally mirrored into the authoritative Milk SOLD
disposition ledger so Finance and Milk remain synchronized.
"""
from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.api.dependencies import get_container
from dairyos.api.reference_data import GOVERNED
from dairyos.api.tmr import (
    is_tmr_catalog_row,
    tmr_default_catalog_names,
)
from dairyos.data.models.feed_inventory_item import FeedInventoryItem
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.production.services.milk_reconciliation_service import (
    MilkReconciliationService,
)
from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.finance.expense_taxonomy import (
    MASTER_CATEGORIES,
    all_items,
    legacy_category,
    valid_item,
)
from dairyos.finance.profitability.services.feed_opex_cost_service import (
    FeedOpexCostService,
)

router = APIRouter(prefix="/farm/finance-ledger", tags=["finance-ledger"])

VALID_STATUSES = {
    "RECORDED",
    "RECEIVED",
    "RECEIVABLE",
    "PAID",
    "PAYABLE",
    "VOID",
}

ALLOWED_STATUS_TRANSITIONS = {
    "RECORDED": frozenset({"RECORDED", "PAYABLE", "RECEIVABLE", "VOID"}),
    "PAYABLE": frozenset({"PAYABLE", "PAID", "VOID"}),
    "RECEIVABLE": frozenset({"RECEIVABLE", "RECEIVED", "VOID"}),
    "PAID": frozenset({"PAID", "VOID"}),
    "RECEIVED": frozenset({"RECEIVED", "VOID"}),
    "VOID": frozenset({"VOID"}),
}

SETTLED_STATUSES = frozenset({"PAID", "RECEIVED"})

MONEY_QUANTUM = Decimal("0.01")
RATE_QUANTUM = Decimal("0.000001")


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _rate(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(
        RATE_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


class FinanceLedgerEntry(BaseModel):
    transaction_type: str = "EXPENSE"
    category: str | None = None
    amount: Decimal | None = Field(default=None, ge=0)
    master_category: str | None = None
    sub_category: str | None = None
    custom_specification: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    unit_rate: Decimal | None = Field(default=None, gt=0)
    transaction_date: date | None = None
    payment_method: str | None = None
    counterparty: str | None = None
    reference: str | None = None
    notes: str | None = None
    status: str = "RECORDED"
    currency: str = "PKR"
    due_date: date | None = None


class FinanceLedgerEdit(BaseModel):
    category: str | None = None
    amount: Decimal | None = Field(default=None, ge=0)
    master_category: str | None = None
    sub_category: str | None = None
    custom_specification: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    unit_rate: Decimal | None = Field(default=None, gt=0)
    transaction_date: date | None = None
    payment_method: str | None = None
    counterparty: str | None = None
    reference: str | None = None
    notes: str | None = None
    status: str | None = None
    due_date: date | None = None


class FinanceStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
    due_date: date | None = None


def _row_dict(row: FinancialTransaction) -> dict:
    return {
        "id": row.id,
        "transaction_type": row.transaction_type,
        "category": row.category,
        "master_category": row.master_category,
        "sub_category": row.sub_category,
        "custom_specification": row.custom_specification,
        "amount": float(row.amount or 0),
        "quantity": row.quantity,
        "unit": row.unit,
        "unit_rate": row.unit_rate,
        "date": row.transaction_date.date().isoformat()
        if row.transaction_date
        else None,
        "transaction_date": row.transaction_date.date().isoformat()
        if row.transaction_date
        else None,
        "reference": row.reference,
        "payment_method": row.payment_method,
        "counterparty": row.counterparty,
        "vendor_name": row.counterparty,
        "notes": row.notes,
        "status": row.status or "RECORDED",
        "currency": row.currency,
        "due_date": row.due_date.isoformat() if row.due_date else None,
        "settled_date": (
            row.settled_date.isoformat() if row.settled_date else None
        ),
        "payroll_record_id": getattr(row, "payroll_record_id", None),
    }



def _is_governed_tmr_feed_item(item_name: str | None) -> bool:
    name = str(item_name or "").strip()
    if not name:
        return False
    if name in tmr_default_catalog_names():
        return True

    probe = RepositoryFactory.create()
    try:
        row = probe.feed_inventory_items().get_by_item(name)
        return bool(
            row is not None
            and bool(getattr(row, "active", True))
            and is_tmr_catalog_row(row)
        )
    finally:
        probe.close()

EQUIPMENT_PURCHASE_ITEM = "Equipment Purchase"


def _validate_expense_payload(
    entry: FinanceLedgerEntry | FinanceLedgerEdit,
    transaction_type: str,
) -> tuple[Decimal, str | None]:
    if transaction_type not in classifier.EXPENSE_TYPES:
        if entry.amount is None:
            raise HTTPException(
                status_code=422,
                detail="amount is required for non-expense entries.",
            )
        return _money(entry.amount), entry.category

    if entry.master_category not in MASTER_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail="master_category must be FEED or OPEX.",
        )

    if not entry.sub_category:
        raise HTTPException(
            status_code=422,
            detail=(
                "sub_category is not valid for "
                "the selected master_category."
            ),
        )

    if entry.master_category == "FEED":
        valid_sub_category = (
            entry.sub_category == "Other"
            or _is_governed_tmr_feed_item(entry.sub_category)
        )
    else:
        valid_sub_category = (
            valid_item(
                entry.master_category,
                entry.sub_category,
            )
            or (
                entry.master_category == "OPEX"
                and entry.sub_category
                == EQUIPMENT_PURCHASE_ITEM
            )
        )

    if not valid_sub_category:
        raise HTTPException(
            status_code=422,
            detail=(
                "sub_category is not valid for "
                "the selected master_category."
            ),
        )

    custom = (entry.custom_specification or "").strip()

    custom_name_required = entry.sub_category in {
        "Other",
        EQUIPMENT_PURCHASE_ITEM,
    }

    if custom_name_required and not custom:
        raise HTTPException(
            status_code=422,
            detail=(
                "custom_specification is required for "
                "Other and Equipment Purchase."
            ),
        )

    if not custom_name_required and custom:
        raise HTTPException(
            status_code=422,
            detail=(
                "custom_specification is only allowed for "
                "Other or Equipment Purchase."
            ),
        )

    if entry.quantity is not None and not entry.unit:
        raise HTTPException(
            status_code=422,
            detail="unit is required when quantity is supplied.",
        )

    if entry.quantity is not None and entry.unit_rate is None:
        raise HTTPException(
            status_code=422,
            detail="unit_rate is required when quantity is supplied.",
        )

    if entry.quantity is not None:
        amount = (
            Decimal(str(entry.quantity)) * Decimal(entry.unit_rate)
        ).quantize(
            MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
    elif entry.amount is not None:
        amount = _money(entry.amount)
    else:
        raise HTTPException(
            status_code=422,
            detail="Provide quantity + unit_rate or a direct amount.",
        )

    if amount <= 0:
        raise HTTPException(
            status_code=422,
            detail="Expense amount must be greater than zero.",
        )

    if (
        entry.master_category == "OPEX"
        and entry.sub_category == EQUIPMENT_PURCHASE_ITEM
    ):
        return amount, "EQUIPMENT"

    return amount, legacy_category(
        entry.master_category,
        entry.sub_category,
    )


def _validate_dates(
    transaction_date: date | None,
    due_date: date | None,
) -> None:
    if transaction_date and due_date and due_date < transaction_date:
        raise HTTPException(
            status_code=422,
            detail="due_date cannot be earlier than transaction_date.",
        )


def _validate_transition(
    current_status: str | None,
    requested_status: str,
) -> str:
    current = (current_status or "RECORDED").strip().upper()
    requested = requested_status.strip().upper()

    if requested not in VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail="Unsupported financial status.",
        )

    allowed = ALLOWED_STATUS_TRANSITIONS.get(
        current,
        frozenset(),
    )

    if requested not in allowed:
        raise HTTPException(
            status_code=409,
            detail=(
                "Invalid financial status transition: "
                f"{current} -> {requested}."
            ),
        )

    return requested


def _require_void_reason(
    status: str,
    reason: str | None,
) -> None:
    if status == "VOID" and not (reason or "").strip():
        raise HTTPException(
            status_code=422,
            detail="A reason is required to void a financial transaction.",
        )


def _append_status_transition(
    row: FinancialTransaction,
    current_status: str,
    next_status: str,
    *,
    reason: str | None = None,
) -> None:
    """Append durable lifecycle evidence without replacing operator notes."""
    if current_status == next_status:
        return

    stamp = datetime.now(UTC).isoformat()
    entry = (
        f"STATUS_TRANSITION_AT={stamp} "
        f"FROM={current_status} TO={next_status}"
    )
    if (reason or "").strip():
        entry += f" REASON={reason.strip()}"

    row.notes = (
        f"{row.notes or ''}\n{entry}"
    ).strip()


def _age_bucket(
    due_date: date | None,
    as_of: date | None = None,
) -> str:
    if due_date is None:
        return "NO_DUE_DATE"

    today = as_of or date.today()
    days_overdue = (today - due_date).days

    if days_overdue <= 0:
        return "CURRENT"
    if days_overdue <= 30:
        return "1_30"
    if days_overdue <= 60:
        return "31_60"
    if days_overdue <= 90:
        return "61_90"

    return "90_PLUS"


def _ageing_payload(
    rows: list[FinancialTransaction],
) -> dict:
    as_of = date.today()

    outstanding = [
        row
        for row in rows
        if row.status == "PAYABLE"
    ]

    total = sum(
        float(row.amount or 0)
        for row in outstanding
    )

    overdue = sum(
        float(row.amount or 0)
        for row in outstanding
        if row.due_date and row.due_date < as_of
    )

    buckets = {
        "CURRENT": 0.0,
        "1_30": 0.0,
        "31_60": 0.0,
        "61_90": 0.0,
        "90_PLUS": 0.0,
        "NO_DUE_DATE": 0.0,
    }

    suppliers: dict[str, float] = {}

    for row in outstanding:
        amount = float(row.amount or 0)
        buckets[_age_bucket(row.due_date, as_of)] += amount

        supplier = row.counterparty or "Unspecified Supplier"
        suppliers[supplier] = (
            suppliers.get(supplier, 0.0) + amount
        )

    return {
        "as_of": as_of.isoformat(),
        "outstanding_total": total,
        "overdue_total": overdue,
        "count": len(outstanding),
        "ageing_buckets": buckets,
        "supplier_rollup": [
            {
                "supplier": supplier,
                "outstanding": amount,
            }
            for supplier, amount in sorted(
                suppliers.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ],
        "transactions": [
            {
                **_row_dict(row),
                "days_overdue": (
                    max(0, (as_of - row.due_date).days)
                    if row.due_date
                    else None
                ),
                "age_bucket": _age_bucket(
                    row.due_date,
                    as_of,
                ),
            }
            for row in sorted(
                outstanding,
                key=lambda item: (
                    item.due_date or date.max,
                    item.transaction_date or datetime.min,
                ),
            )
        ],
    }


def _factory(container):
    factory = getattr(
        container,
        "repository_factory",
        None,
    )

    if factory is None:
        raise HTTPException(
            status_code=503,
            detail="Canonical repository factory is not available",
        )

    return factory



def _finance_feed_item_name(
    master_category: str | None,
    sub_category: str | None,
    custom_specification: str | None,
) -> str | None:
    if str(master_category or "").strip().upper() != "FEED":
        return None

    sub = str(sub_category or "").strip()

    if not sub:
        return None

    if sub == "Other":
        custom = str(custom_specification or "").strip()
        return custom or None

    return sub


def _ensure_feed_catalog_authority(
    *,
    factory,
    transaction: FinancialTransaction,
) -> FeedInventoryItem | None:
    """
    Ensure a Finance FEED expense has a matching Feed catalog authority.

    Finance remains the sole purchase-quantity authority. This function
    creates/reactivates only the catalog identity; it deliberately does
    not create an InventoryTransaction PURCHASE/RECEIPT movement.
    """

    transaction_type = classifier.normalize_transaction_type(
        transaction.transaction_type
    )

    if transaction_type not in classifier.EXPENSE_TYPES:
        return None

    item_name = _finance_feed_item_name(
        transaction.master_category,
        transaction.sub_category,
        transaction.custom_specification,
    )

    if not item_name:
        return None

    quantity = float(transaction.quantity or 0)

    if quantity <= 0:
        return None

    unit = str(transaction.unit or "").strip()

    if not unit:
        raise HTTPException(
            status_code=422,
            detail=(
                "Finance Feed purchases require a unit before "
                "Feed catalog synchronization."
            ),
        )

    repository = factory.feed_inventory_items()
    existing = repository.get_by_item(item_name)

    if existing is not None:
        existing_unit = str(existing.unit or "").strip()

        if existing_unit and existing_unit != unit:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Feed catalog unit mismatch for '{item_name}': "
                    f"catalog uses {existing_unit}, Finance uses {unit}."
                ),
            )

        changed = False

        if not existing_unit:
            existing.unit = unit
            changed = True

        if not existing.active:
            existing.active = True
            changed = True

        if changed:
            factory.session.add(existing)
            factory.session.flush()

        return existing

    row = FeedInventoryItem(
        item=item_name,
        category="FEED",
        unit=unit,
        reorder_level=0,
        active=True,
        notes="Established automatically from Finance Feed authority.",
    )

    factory.session.add(row)
    factory.session.flush()

    return row

def _linked_milk_sale(
    factory,
    finance_id: int,
    *,
    lock: bool = False,
) -> MilkDisposition | None:
    query = (
        factory.session.query(MilkDisposition)
        .filter(
            MilkDisposition.sale_id == f"FIN-{finance_id}",
        )
    )

    if lock:
        query = query.with_for_update()

    return query.first()


def _sync_milk_sale(
    *,
    factory,
    transaction: FinancialTransaction,
    entry: FinanceLedgerEntry,
    transaction_type: str,
    status: str,
) -> MilkDisposition | None:
    """Create the Milk SOLD record corresponding to a Finance sale."""

    if transaction_type not in classifier.INCOME_TYPES:
        return None

    if str(transaction.category or "").upper() != "MILK_SALES":
        return None

    quantity = (
        float(entry.quantity)
        if entry.quantity is not None
        else 0.0
    )

    if quantity <= 0:
        raise HTTPException(
            status_code=422,
            detail="Milk Sales requires a positive quantity in litres.",
        )

    production_date = (
        entry.transaction_date
        or date.today()
    )

    existing = _linked_milk_sale(
        factory,
        transaction.id,
    )

    if existing is not None:
        return existing

    production_repository = factory.milk()

    dispositions = (
        factory.milk_dispositions()
        .get_by_date(production_date)
    )

    production_basis = MilkReconciliationService._production_total(
        production_date,
        production_repository=production_repository,
    )

    try:
        MilkReconciliationService.validate_disposition_quantity(
            production_basis=production_basis,
            dispositions=dispositions,
            disposition_type="SOLD",
            quantity_litres=quantity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    amount = _money(transaction.amount)

    if amount <= 0:
        raise HTTPException(
            status_code=422,
            detail="Milk Sales amount must be greater than zero.",
        )

    price_per_litre = (
        amount / Decimal(str(quantity))
    ).quantize(
        RATE_QUANTUM,
        rounding=ROUND_HALF_UP,
    )

    amount_received = (
        amount
        if status in SETTLED_STATUSES
        else Decimal("0.00")
    )

    disposition = MilkDisposition(
        production_date=production_date,
        disposition_type="SOLD",
        quantity_litres=quantity,
        sale_id=f"FIN-{transaction.id}",
        counterparty=transaction.counterparty,
        selling_price_per_litre=price_per_litre,
        amount_due=amount,
        amount_received=amount_received,
        notes=transaction.notes,
        recorded_by="Finance UI",
        status="RECORDED",
    )

    factory.session.add(disposition)
    factory.session.flush()

    return disposition


def _sync_existing_milk_sale_status(
    *,
    factory,
    transaction: FinancialTransaction,
) -> None:
    """Keep an existing Milk SOLD disposition aligned with Finance status."""

    if str(transaction.category or "").upper() != "MILK_SALES":
        return

    disposition = _linked_milk_sale(
        factory,
        transaction.id,
    )

    if disposition is None:
        return

    status = str(
        transaction.status or "RECORDED",
    ).upper()

    if status != "VOID":
        production_date = transaction.transaction_date.date()
        quantity = float(transaction.quantity or 0)
        if quantity <= 0:
            raise HTTPException(status_code=422, detail="Milk Sales requires a positive quantity in litres.")
        try:
            MilkReconciliationService.validate_disposition_quantity(
                production_basis=MilkReconciliationService._production_total(
                    production_date, production_repository=factory.milk(),
                ),
                dispositions=factory.milk_dispositions().get_by_date(production_date),
                disposition_type="SOLD", quantity_litres=quantity, exclude_id=disposition.id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        disposition.production_date = production_date
        disposition.quantity_litres = quantity
        disposition.counterparty = transaction.counterparty
        disposition.amount_due = Decimal(str(transaction.amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        disposition.selling_price_per_litre = (
            disposition.amount_due / Decimal(str(quantity))
        ).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP,
        )
        transaction.unit_rate = disposition.selling_price_per_litre

    if status in SETTLED_STATUSES:
        disposition.amount_received = disposition.amount_due
        disposition.status = "RECORDED"

    elif status == "RECEIVABLE":
        disposition.amount_received = 0.0
        disposition.status = "RECORDED"

    elif status == "VOID":
        disposition.status = "VOID"
        disposition.notes = transaction.notes

    disposition.updated_at = datetime.now(UTC)
    factory.session.add(disposition)


@router.get("")
def list_finance_ledger(
    container=Depends(get_container),
):
    factory = _factory(container)
    rows = factory.finance().get_all()

    return {
        "data_status": "LIVE_PERSISTED_DATA",
        "transactions": [
            _row_dict(row)
            for row in sorted(
                rows,
                key=lambda r: r.transaction_date or datetime.min,
                reverse=True,
            )
        ],
    }


@router.post("")
def create_finance_ledger_entry(
    entry: FinanceLedgerEntry,
    container=Depends(get_container),
):
    transaction_type = classifier.normalize_transaction_type(
        entry.transaction_type
    )

    if transaction_type not in GOVERNED[
        "financial_transaction_types"
    ]:
        raise HTTPException(
            status_code=422,
            detail="Unsupported transaction_type.",
        )

    amount, legacy_category_value = _validate_expense_payload(
        entry,
        transaction_type,
    )

    if (
        entry.payment_method is not None
        and entry.payment_method not in GOVERNED["payment_types"]
    ):
        raise HTTPException(
            status_code=422,
            detail="Unsupported payment_method.",
        )

    status = entry.status.strip().upper()

    if status not in {
        "RECORDED",
        "PAYABLE",
        "RECEIVABLE",
        "PAID",
        "RECEIVED",
    }:
        raise HTTPException(
            status_code=422,
            detail=(
                "New financial transactions must begin in "
                "RECORDED, PAYABLE, RECEIVABLE, PAID or RECEIVED state."
            ),
        )

    _validate_dates(
        entry.transaction_date,
        entry.due_date,
    )

    if (
        status in {"PAYABLE", "RECEIVABLE"}
        and entry.due_date is None
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "due_date is required for PAYABLE or "
                "RECEIVABLE transactions."
            ),
        )

    if transaction_type in classifier.EXPENSE_TYPES:
        category_value = (
            legacy_category_value
            or "OTHER_OPERATING"
        )
    else:
        category_value = (
            entry.category
            or (
                "MILK_SALES"
                if transaction_type in classifier.INCOME_TYPES
                else "OTHER_REVENUE"
            )
        )

    is_milk_sale = (
        transaction_type in classifier.INCOME_TYPES
        and str(category_value).upper() == "MILK_SALES"
    )

    if is_milk_sale:
        if entry.quantity is None or float(entry.quantity) <= 0:
            raise HTTPException(
                status_code=422,
                detail="Milk Sales requires a positive quantity in litres.",
            )

        quantity_value = float(entry.quantity)
        unit_value = "litre"
        unit_rate_value = (
            Decimal(amount) / Decimal(str(quantity_value))
        ).quantize(
            RATE_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
    else:
        quantity_value = (
            entry.quantity
            if transaction_type in classifier.EXPENSE_TYPES
            else None
        )
        unit_value = (
            entry.unit
            if transaction_type in classifier.EXPENSE_TYPES
            else None
        )
        unit_rate_value = (
            entry.unit_rate
            if transaction_type in classifier.EXPENSE_TYPES
            else None
        )

    factory = _factory(container)
    session = factory.session

    transaction = FinancialTransaction(
        transaction_type=transaction_type,
        category=category_value,
        amount=amount,
        reference=(
            entry.reference
            or entry.counterparty
            or entry.notes
            or ""
        ),
        payment_method=entry.payment_method,
        counterparty=entry.counterparty,
        notes=entry.notes,
        currency=entry.currency,
        status=status,
        master_category=(
            entry.master_category
            if transaction_type in classifier.EXPENSE_TYPES
            else None
        ),
        sub_category=(
            entry.sub_category
            if transaction_type in classifier.EXPENSE_TYPES
            else None
        ),
        custom_specification=(
            entry.custom_specification
            if transaction_type in classifier.EXPENSE_TYPES
            else None
        ),
        quantity=quantity_value,
        unit=unit_value,
        unit_rate=unit_rate_value,
        due_date=entry.due_date,
        settled_date=(
            date.today()
            if status in SETTLED_STATUSES
            else None
        ),
    )

    if entry.transaction_date is not None:
        transaction.transaction_date = datetime.combine(
            entry.transaction_date,
            datetime.min.time(),
        )

    session.add(transaction)
    session.flush()

    try:
        _ensure_feed_catalog_authority(
            factory=factory,
            transaction=transaction,
        )

        _sync_milk_sale(
            factory=factory,
            transaction=transaction,
            entry=entry,
            transaction_type=transaction_type,
            status=status,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    session.refresh(transaction)

    return _row_dict(transaction)


@router.get("/taxonomy")
def finance_taxonomy():
    # TMR is the master ingredient-name authority.
    # Lazy import avoids the Finance/TMR bootstrap cycle.
    from dairyos.api.tmr import (
        governed_tmr_catalog_names,
    )

    probe = RepositoryFactory.create()

    try:
        feed_items = governed_tmr_catalog_names(
            probe
        )
    finally:
        probe.close()

    # Other is an explicit transaction mechanism, not a second
    # named feed catalog. All named FEED options come from TMR.
    if "Other" in feed_items:
        feed_items = [
            item
            for item in feed_items
            if item != "Other"
        ]

    feed_items.append("Other")

    taxonomies = dict(
        GOVERNED["finance_expense_taxonomy"]
    )

    # Preserve the grouped taxonomy response contract consumed
    # by FinanceTab. TMR remains the content authority.
    taxonomies["FEED"] = {
        "TMR_INGREDIENTS": list(feed_items),
    }

    # Preserve existing grouped OPEX taxonomy without mutating
    # the governed reference-data object.
    opex_groups = dict(
        taxonomies.get("OPEX") or {}
    )

    # Equipment Purchase remains an explicit Finance OPEX action.
    opex_groups["EQUIPMENT"] = [
        EQUIPMENT_PURCHASE_ITEM
    ]

    taxonomies["OPEX"] = opex_groups

    opex_items = [
        *all_items("OPEX")
    ]

    if EQUIPMENT_PURCHASE_ITEM not in opex_items:
        opex_items.append(
            EQUIPMENT_PURCHASE_ITEM
        )

    return {
        "master_categories": sorted(
            MASTER_CATEGORIES
        ),
        "taxonomies": taxonomies,
        "items": {
            "FEED": feed_items,
            "OPEX": opex_items,
        },
    }


@router.get("/cost-of-production")
def finance_cost_of_production(
    days: int = Query(default=30, ge=1, le=366),
    container=Depends(get_container),
):
    factory = _factory(container)

    return FeedOpexCostService().evaluate(
        factory.milk().get_all(),
        factory.finance().get_all(),
        days=days,
    )


@router.get("/ageing")
def finance_ledger_ageing(
    container=Depends(get_container),
):
    factory = _factory(container)
    rows = factory.finance().get_all()

    return _ageing_payload(rows)


@router.get("/profitability/feed-opex")
def feed_opex_profitability(
    period_start: date = Query(...),
    period_end: date = Query(...),
    container=Depends(get_container),
):
    if period_end < period_start:
        raise HTTPException(
            status_code=422,
            detail="period_end cannot be earlier than period_start.",
        )

    # FeedOpexCostService is deliberately a stateless calculation service.
    # Keep this route on the same persisted-input contract as the adjacent
    # cost-of-production route instead of treating the RuntimeContainer as a
    # service instance.
    factory = _factory(container)
    days = (period_end - period_start).days + 1

    def in_period(row, field):
        value = getattr(row, field, None)
        if isinstance(value, datetime):
            value = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
            value = value.date()
        return value is not None and period_start <= value <= period_end

    return FeedOpexCostService().evaluate(
        [row for row in factory.milk().get_all() if in_period(row, "production_date")],
        [row for row in factory.finance().get_all() if in_period(row, "transaction_date")],
        days=days,
        now=datetime.combine(period_end, datetime.max.time(), tzinfo=UTC),
    )


@router.patch("/{transaction_id}")
def edit_finance_ledger_entry(
    transaction_id: int,
    payload: FinanceLedgerEdit,
    container=Depends(get_container),
):
    runtime_factory = _factory(container)

    if getattr(runtime_factory, "session", None) is None:
        return _edit_finance_ledger_entry(
            transaction_id,
            payload,
            runtime_factory,
        )

    # Cross-module Finance/Milk amendments require an isolated application
    # transaction. RepositoryFactory.create() is the governed persistence
    # composition boundary; do not borrow the runtime's long-lived session.
    factory = RepositoryFactory.create()
    try:
        with factory.session.begin():
            return _edit_finance_ledger_entry(
                transaction_id,
                payload,
                factory,
            )
    finally:
        factory.close()


def _edit_finance_ledger_entry(transaction_id, payload, factory):
    repository = factory.finance()

    # Canonical cross-module lock order:
    # MilkDisposition first, then primary FinancialTransaction.
    linked_disposition = _linked_milk_sale(
        factory,
        transaction_id,
        lock=True,
    )

    row = (
        factory.session.query(FinancialTransaction)
        .filter_by(id=transaction_id)
        .with_for_update()
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Financial transaction not found.",
        )

    current_status = (
        row.status or "RECORDED"
    ).strip().upper()

    if current_status == "VOID":
        raise HTTPException(
            status_code=409,
            detail="VOID transactions cannot be edited.",
        )

    if current_status in SETTLED_STATUSES:
        supplied_fields = set(
            payload.model_dump(exclude_unset=True)
        )

        if supplied_fields:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Settled transactions in "
                    f"{current_status} state are immutable; "
                    "create a governed correction entry instead."
                ),
            )

        return _row_dict(row)

    transaction_type = classifier.normalize_transaction_type(
        row.transaction_type
    )

    if transaction_type in classifier.EXPENSE_TYPES:
        master = (
            payload.master_category
            if payload.master_category is not None
            else row.master_category
        )

        sub = (
            payload.sub_category
            if payload.sub_category is not None
            else row.sub_category
        )

        custom = (
            payload.custom_specification
            if payload.custom_specification is not None
            else row.custom_specification
        )

        values = payload.model_dump(
            exclude_unset=True
        )

        values.update(
            {
                "master_category": master,
                "sub_category": sub,
                "custom_specification": custom,
                "quantity": (
                    payload.quantity
                    if payload.quantity is not None
                    else row.quantity
                ),
                "unit": (
                    payload.unit
                    if payload.unit is not None
                    else row.unit
                ),
                "unit_rate": (
                    payload.unit_rate
                    if payload.unit_rate is not None
                    else row.unit_rate
                ),
                "amount": (
                    payload.amount
                    if payload.amount is not None
                    else row.amount
                ),
            }
        )

        temp = FinanceLedgerEdit(**values)

        amount, legacy_category_value = (
            _validate_expense_payload(
                temp,
                transaction_type,
            )
        )

        row.master_category = master
        row.sub_category = sub
        row.custom_specification = custom
        row.quantity = temp.quantity
        row.unit = temp.unit
        row.unit_rate = temp.unit_rate
        row.category = (
            legacy_category_value
            or row.category
        )

    else:
        amount = (
            payload.amount
            if payload.amount is not None
            else row.amount
        )

        if amount <= 0:
            raise HTTPException(
                status_code=422,
                detail="amount must be greater than zero.",
            )

    transaction_date = (
        payload.transaction_date
        or (
            row.transaction_date.date()
            if row.transaction_date
            else None
        )
    )

    due_date = (
        payload.due_date
        if payload.due_date is not None
        else row.due_date
    )

    _validate_dates(
        transaction_date,
        due_date,
    )

    status = _validate_transition(
        current_status,
        payload.status
        if payload.status
        else current_status,
    )

    _require_void_reason(
        status,
        payload.notes,
    )

    if (
        status in {"PAYABLE", "RECEIVABLE"}
        and due_date is None
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "due_date is required for PAYABLE or "
                "RECEIVABLE transactions."
            ),
        )

    if (
        payload.category is not None
        and transaction_type not in classifier.EXPENSE_TYPES
    ):
        row.category = payload.category

    if payload.transaction_date is not None:
        row.transaction_date = datetime.combine(
            payload.transaction_date,
            datetime.min.time(),
        )

    if (
        payload.amount is not None
        or transaction_type in classifier.EXPENSE_TYPES
    ):
        row.amount = amount

    if payload.payment_method is not None:
        if payload.payment_method not in GOVERNED[
            "payment_types"
        ]:
            raise HTTPException(
                status_code=422,
                detail="Unsupported payment_method.",
            )

        row.payment_method = payload.payment_method

    if payload.counterparty is not None:
        row.counterparty = payload.counterparty

    if payload.reference is not None:
        row.reference = payload.reference

    if payload.notes is not None:
        row.notes = payload.notes

    _append_status_transition(
        row,
        current_status,
        status,
        reason=payload.notes if status == "VOID" else None,
    )
    row.status = status
    row.due_date = due_date

    if (
        status in SETTLED_STATUSES
        and row.settled_date is None
    ):
        row.settled_date = date.today()

    if status not in SETTLED_STATUSES:
        row.settled_date = None

    if str(row.category or "").upper() == "MILK_SALES" and (payload.quantity is not None or payload.unit_rate is not None):
        row.quantity = payload.quantity if payload.quantity is not None else row.quantity
        row.unit_rate = payload.unit_rate if payload.unit_rate is not None else row.unit_rate
        calculated = (Decimal(str(row.quantity)) * Decimal(str(row.unit_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if payload.amount is not None and Decimal(str(payload.amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) != calculated:
            raise HTTPException(status_code=422, detail="Milk sale amount must equal quantity times rate.")
        row.amount = calculated

    factory.session.add(row)
    _sync_existing_milk_sale_status(
        factory=factory,
        transaction=row,
    )

    try:
        _ensure_feed_catalog_authority(
            factory=factory,
            transaction=row,
        )
    except Exception:
        factory.session.rollback()
        raise

    factory.session.flush()

    return _row_dict(row)


@router.delete("/{transaction_id}")
def delete_finance_ledger_entry(
    transaction_id: int,
    container=Depends(get_container),
):
    factory = _factory(container)
    repository = factory.finance()

    try:
        repository.delete(transaction_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@router.post("/{transaction_id}/status")
def update_finance_ledger_status(
    transaction_id: int,
    payload: FinanceStatusUpdate,
    container=Depends(get_container),
):
    runtime_factory = _factory(container)

    if getattr(runtime_factory, "session", None) is None:
        return _update_finance_ledger_status(
            transaction_id,
            payload,
            runtime_factory,
        )

    factory = RepositoryFactory.create()
    try:
        with factory.session.begin():
            return _update_finance_ledger_status(
                transaction_id,
                payload,
                factory,
            )
    finally:
        factory.close()


def _update_finance_ledger_status(transaction_id, payload, factory):
    repository = factory.finance()

    # Use the same lock order as Milk-side mutations.
    linked_disposition = _linked_milk_sale(
        factory,
        transaction_id,
        lock=True,
    )

    row = (
        factory.session.query(FinancialTransaction)
        .filter_by(id=transaction_id)
        .with_for_update()
        .first()
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Financial transaction not found.",
        )

    current_status = (row.status or "RECORDED").strip().upper()
    status = _validate_transition(
        current_status,
        payload.status,
    )

    _require_void_reason(
        status,
        payload.reason,
    )

    if payload.due_date is not None:
        transaction_date = (
            row.transaction_date.date()
            if row.transaction_date
            else None
        )

        _validate_dates(
            transaction_date,
            payload.due_date,
        )

        row.due_date = payload.due_date

    if (
        status in {"PAYABLE", "RECEIVABLE"}
        and row.due_date is None
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "due_date is required for PAYABLE or "
                "RECEIVABLE transactions."
            ),
        )

    _append_status_transition(
        row,
        current_status,
        status,
        reason=payload.reason,
    )
    row.status = status
    if status in SETTLED_STATUSES:
        row.settled_date = row.settled_date or date.today()
    elif not (
        status == "VOID"
        and current_status in SETTLED_STATUSES
    ):
        row.settled_date = None

    factory.session.add(row)

    _sync_existing_milk_sale_status(
        factory=factory,
        transaction=row,
    )

    factory.session.flush()

    return _row_dict(row)
