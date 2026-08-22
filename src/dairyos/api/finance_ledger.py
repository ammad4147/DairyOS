"""Persistent Finance ledger API for the Feed/OPEX vertical slice."""
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


class FinanceStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


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
        "date": row.transaction_date.isoformat() if row.transaction_date else None,
        "transaction_date": row.transaction_date.isoformat() if row.transaction_date else None,
        "reference": row.reference,
        "payment_method": row.payment_method,
        "counterparty": row.counterparty,
        "vendor_name": row.counterparty,
        "notes": row.notes,
        "status": row.status or "RECORDED",
        "currency": row.currency,
    }


def _validate_expense_payload(entry: FinanceLedgerEntry) -> tuple[float, str | None]:
    transaction_type = classifier.normalize_transaction_type(entry.transaction_type)
    if transaction_type not in GOVERNED["financial_transaction_types"]:
        raise HTTPException(status_code=422, detail="Unsupported transaction_type.")

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
    amount, legacy_category_value = _validate_expense_payload(entry)
    transaction_type = classifier.normalize_transaction_type(entry.transaction_type)

    if entry.payment_method is not None and entry.payment_method not in GOVERNED["payment_types"]:
        raise HTTPException(status_code=422, detail="Unsupported payment_method.")

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
            status=entry.status,
            master_category=entry.master_category if transaction_type in classifier.EXPENSE_TYPES else None,
            sub_category=entry.sub_category if transaction_type in classifier.EXPENSE_TYPES else None,
            custom_specification=entry.custom_specification if transaction_type in classifier.EXPENSE_TYPES else None,
            quantity=entry.quantity if transaction_type in classifier.EXPENSE_TYPES else None,
            unit=entry.unit if transaction_type in classifier.EXPENSE_TYPES else None,
            unit_rate=entry.unit_rate if transaction_type in classifier.EXPENSE_TYPES else None,
        )
        if entry.transaction_date is not None:
            transaction.transaction_date = datetime.combine(entry.transaction_date, datetime.min.time())

        saved = factory.finance().add(transaction)
        return _row_dict(saved)
    finally:
        factory.close()


@router.post("/{transaction_id}/status")
def update_finance_status(transaction_id: int, payload: FinanceStatusUpdate):
    status = payload.status.strip().upper()
    if status not in {"RECORDED", "RECEIVED", "RECEIVABLE", "PAID", "PAYABLE", "VOID"}:
        raise HTTPException(status_code=422, detail="Unsupported financial status.")

    factory = RepositoryFactory.create()
    try:
        row = factory.finance().get_by_id(transaction_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Financial transaction not found.")
        row.status = status
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
