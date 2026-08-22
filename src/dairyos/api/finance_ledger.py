"""Persistent Finance ledger API.

Finance remains one unified ledger. Feed/OPEX are analytical dimensions on
expense rows; credit-control adds due/settlement dates and ageing without
creating a second ledger.
"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from dairyos.api.reference_data import GOVERNED
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.finance.expense_taxonomy import MASTER_CATEGORIES, all_items, legacy_category, valid_item
from dairyos.finance.profitability.services.feed_opex_cost_service import FeedOpexCostService

router = APIRouter(prefix="/farm/finance-ledger", tags=["finance-ledger"])

VALID_STATUSES = {"RECORDED", "RECEIVED", "RECEIVABLE", "PAID", "PAYABLE", "VOID"}


class FinanceLedgerEntry(BaseModel):
    transaction_type: str = "EXPENSE"
    category: str | None = None
    amount: float | None = Field(default=None, ge=0)
    master_category: str | None = None
    sub_category: str | None = None
    custom_specification: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    unit_rate: float | None = Field(default=None, gt=0)
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
    amount: float | None = Field(default=None, ge=0)
    master_category: str | None = None
    sub_category: str | None = None
    custom_specification: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    unit_rate: float | None = Field(default=None, gt=0)
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
        "date": row.transaction_date.date().isoformat() if row.transaction_date else None,
        "transaction_date": row.transaction_date.date().isoformat() if row.transaction_date else None,
        "reference": row.reference,
        "payment_method": row.payment_method,
        "counterparty": row.counterparty,
        "vendor_name": row.counterparty,
        "notes": row.notes,
        "status": row.status or "RECORDED",
        "currency": row.currency,
        "due_date": row.due_date.isoformat() if row.due_date else None,
        "settled_date": row.settled_date.isoformat() if row.settled_date else None,
    }


def _validate_expense_payload(entry: FinanceLedgerEntry | FinanceLedgerEdit, transaction_type: str) -> tuple[float, str | None]:
    if transaction_type not in classifier.EXPENSE_TYPES:
        if entry.amount is None:
            raise HTTPException(status_code=422, detail="amount is required for non-expense entries.")
        return float(entry.amount), entry.category

    if entry.master_category not in MASTER_CATEGORIES:
        raise HTTPException(status_code=422, detail="master_category must be FEED or OPEX.")
    if not entry.sub_category or not valid_item(entry.master_category, entry.sub_category):
        raise HTTPException(status_code=422, detail="sub_category is not valid for the selected master_category.")

    custom = (entry.custom_specification or "").strip()
    if entry.sub_category == "Other" and not custom:
        raise HTTPException(status_code=422, detail="custom_specification is required when Item is Other.")
    if entry.sub_category != "Other" and custom:
        raise HTTPException(status_code=422, detail="custom_specification is only allowed for Other.")

    if entry.quantity is not None and not entry.unit:
        raise HTTPException(status_code=422, detail="unit is required when quantity is supplied.")
    if entry.quantity is not None and entry.unit_rate is None:
        raise HTTPException(status_code=422, detail="unit_rate is required when quantity is supplied.")

    if entry.quantity is not None:
        amount = float(entry.quantity) * float(entry.unit_rate)
    elif entry.amount is not None:
        amount = float(entry.amount)
    else:
        raise HTTPException(status_code=422, detail="Provide quantity + unit_rate or a direct amount.")
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Expense amount must be greater than zero.")

    return amount, legacy_category(entry.master_category, entry.sub_category)


def _validate_dates(transaction_date: date | None, due_date: date | None) -> None:
    if transaction_date and due_date and due_date < transaction_date:
        raise HTTPException(status_code=422, detail="due_date cannot be earlier than transaction_date.")


def _age_bucket(due_date: date | None, as_of: date | None = None) -> str:
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


def _ageing_payload(rows: list[FinancialTransaction]) -> dict:
    as_of = date.today()
    outstanding = [row for row in rows if row.status == "PAYABLE"]
    total = sum(float(row.amount or 0) for row in outstanding)
    overdue = sum(float(row.amount or 0) for row in outstanding if row.due_date and row.due_date < as_of)
    buckets = {"CURRENT": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "90_PLUS": 0.0, "NO_DUE_DATE": 0.0}
    suppliers: dict[str, float] = {}
    for row in outstanding:
        amount = float(row.amount or 0)
        buckets[_age_bucket(row.due_date, as_of)] += amount
        supplier = row.counterparty or "Unspecified Supplier"
        suppliers[supplier] = suppliers.get(supplier, 0.0) + amount

    return {
        "as_of": as_of.isoformat(),
        "outstanding_total": total,
        "overdue_total": overdue,
        "count": len(outstanding),
        "ageing_buckets": buckets,
        "supplier_rollup": [
            {"supplier": supplier, "outstanding": amount}
            for supplier, amount in sorted(suppliers.items(), key=lambda item: item[1], reverse=True)
        ],
        "transactions": [
            {
                **_row_dict(row),
                "days_overdue": max(0, (as_of - row.due_date).days) if row.due_date else None,
                "age_bucket": _age_bucket(row.due_date, as_of),
            }
            for row in sorted(outstanding, key=lambda item: (item.due_date or date.max, item.transaction_date or datetime.min))
        ],
    }


@router.get("")
def list_finance_ledger():
    factory = RepositoryFactory.create()
    try:
        rows = factory.finance().get_all()
        return {
            "data_status": "LIVE_PERSISTED_DATA",
            "transactions": [
                _row_dict(row)
                for row in sorted(rows, key=lambda r: r.transaction_date or datetime.min, reverse=True)
            ],
        }
    finally:
        factory.close()


@router.post("")
def create_finance_ledger_entry(entry: FinanceLedgerEntry):
    transaction_type = classifier.normalize_transaction_type(entry.transaction_type)
    if transaction_type not in GOVERNED["financial_transaction_types"]:
        raise HTTPException(status_code=422, detail="Unsupported transaction_type.")
    amount, legacy_category_value = _validate_expense_payload(entry, transaction_type)

    if entry.payment_method is not None and entry.payment_method not in GOVERNED["payment_types"]:
        raise HTTPException(status_code=422, detail="Unsupported payment_method.")
    status = entry.status.strip().upper()
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail="Unsupported financial status.")
    _validate_dates(entry.transaction_date, entry.due_date)
    if status in {"PAYABLE", "RECEIVABLE"} and entry.due_date is None:
        raise HTTPException(status_code=422, detail="due_date is required for PAYABLE or RECEIVABLE transactions.")

    if transaction_type in classifier.EXPENSE_TYPES:
        category_value = legacy_category_value or "OTHER_OPERATING"
    else:
        category_value = entry.category or ("MILK_SALES" if transaction_type in classifier.INCOME_TYPES else "OTHER_OPERATING")

    factory = RepositoryFactory.create()
    try:
        transaction = FinancialTransaction(
            transaction_type=transaction_type,
            category=category_value,
            amount=amount,
            reference=entry.reference or entry.counterparty or entry.notes or "",
            payment_method=entry.payment_method,
            counterparty=entry.counterparty,
            notes=entry.notes,
            currency=entry.currency,
            status=status,
            master_category=entry.master_category if transaction_type in classifier.EXPENSE_TYPES else None,
            sub_category=entry.sub_category if transaction_type in classifier.EXPENSE_TYPES else None,
            custom_specification=entry.custom_specification if transaction_type in classifier.EXPENSE_TYPES else None,
            quantity=entry.quantity if transaction_type in classifier.EXPENSE_TYPES else None,
            unit=entry.unit if transaction_type in classifier.EXPENSE_TYPES else None,
            unit_rate=entry.unit_rate if transaction_type in classifier.EXPENSE_TYPES else None,
            due_date=entry.due_date,
            settled_date=date.today() if status in {"PAID", "RECEIVED"} else None,
        )
        if entry.transaction_date is not None:
            transaction.transaction_date = datetime.combine(entry.transaction_date, datetime.min.time())
        saved = factory.finance().add(transaction)
        return _row_dict(saved)
    finally:
        factory.close()


@router.patch("/{transaction_id}")
def edit_finance_ledger_entry(transaction_id: int, payload: FinanceLedgerEdit):
    factory = RepositoryFactory.create()
    try:
        row = factory.finance().get_by_id(transaction_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Financial transaction not found.")
        if row.status == "VOID":
            raise HTTPException(status_code=409, detail="VOID transactions cannot be edited.")

        transaction_type = classifier.normalize_transaction_type(row.transaction_type)
        if transaction_type in classifier.EXPENSE_TYPES:
            master = payload.master_category if payload.master_category is not None else row.master_category
            sub = payload.sub_category if payload.sub_category is not None else row.sub_category
            custom = payload.custom_specification if payload.custom_specification is not None else row.custom_specification
            values = payload.model_dump(exclude_unset=True)
            values.update({
                "master_category": master,
                "sub_category": sub,
                "custom_specification": custom,
                "quantity": payload.quantity if payload.quantity is not None else row.quantity,
                "unit": payload.unit if payload.unit is not None else row.unit,
                "unit_rate": payload.unit_rate if payload.unit_rate is not None else row.unit_rate,
                "amount": payload.amount if payload.amount is not None else row.amount,
            })
            temp = FinanceLedgerEdit(**values)
            amount, legacy_category_value = _validate_expense_payload(temp, transaction_type)
            row.master_category = master
            row.sub_category = sub
            row.custom_specification = custom
            row.quantity = temp.quantity
            row.unit = temp.unit
            row.unit_rate = temp.unit_rate
            row.category = legacy_category_value or row.category
        else:
            amount = payload.amount if payload.amount is not None else row.amount
            if amount <= 0:
                raise HTTPException(status_code=422, detail="amount must be greater than zero.")

        transaction_date = payload.transaction_date or (row.transaction_date.date() if row.transaction_date else None)
        due_date = payload.due_date if payload.due_date is not None else row.due_date
        _validate_dates(transaction_date, due_date)
        status = payload.status.strip().upper() if payload.status else row.status
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=422, detail="Unsupported financial status.")
        if status in {"PAYABLE", "RECEIVABLE"} and due_date is None:
            raise HTTPException(status_code=422, detail="due_date is required for PAYABLE or RECEIVABLE transactions.")

        if payload.category is not None and transaction_type not in classifier.EXPENSE_TYPES:
            row.category = payload.category
        if payload.transaction_date is not None:
            row.transaction_date = datetime.combine(payload.transaction_date, datetime.min.time())
        if payload.amount is not None or transaction_type in classifier.EXPENSE_TYPES:
            row.amount = amount
        if payload.payment_method is not None:
            if payload.payment_method not in GOVERNED["payment_types"]:
                raise HTTPException(status_code=422, detail="Unsupported payment_method.")
            row.payment_method = payload.payment_method
        if payload.counterparty is not None:
            row.counterparty = payload.counterparty
        if payload.reference is not None:
            row.reference = payload.reference
        if payload.notes is not None:
            row.notes = payload.notes
        row.status = status
        row.due_date = due_date
        row.settled_date = date.today() if status in {"PAID", "RECEIVED"} else None

        saved = factory.finance().add(row)
        return _row_dict(saved)
    finally:
        factory.close()


@router.get("/payables")
def list_payables():
    factory = RepositoryFactory.create()
    try:
        rows = factory.finance().get_all()
        return _ageing_payload([row for row in rows if row.status == "PAYABLE"])
    finally:
        factory.close()


@router.post("/{transaction_id}/status")
def update_finance_status(transaction_id: int, payload: FinanceStatusUpdate):
    status = payload.status.strip().upper()
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail="Unsupported financial status.")

    factory = RepositoryFactory.create()
    try:
        row = factory.finance().get_by_id(transaction_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Financial transaction not found.")
        due_date = payload.due_date if payload.due_date is not None else row.due_date
        transaction_date = row.transaction_date.date() if row.transaction_date else None
        _validate_dates(transaction_date, due_date)
        if status in {"PAYABLE", "RECEIVABLE"} and due_date is None:
            raise HTTPException(status_code=422, detail="due_date is required for PAYABLE or RECEIVABLE transactions.")
        row.status = status
        row.due_date = due_date
        row.settled_date = date.today() if status in {"PAID", "RECEIVED"} else None
        if payload.reason:
            row.notes = f"{row.notes or ''}\n[{status}] {payload.reason}".strip()
        saved = factory.finance().add(row)
        return _row_dict(saved)
    finally:
        factory.close()


@router.get("/taxonomy")
def finance_taxonomy():
    return {
        "master_categories": sorted(MASTER_CATEGORIES),
        "taxonomies": GOVERNED["finance_expense_taxonomy"],
        "items": {master: all_items(master) for master in sorted(MASTER_CATEGORIES)},
    }


@router.get("/cost-of-production")
def finance_cost_of_production(days: int = Query(default=30, ge=1, le=366)):
    factory = RepositoryFactory.create()
    try:
        return FeedOpexCostService().evaluate(factory.milk().get_all(), factory.finance().get_all(), days=days)
    finally:
        factory.close()
