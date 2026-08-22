"""Canonical financial transaction-type classification."""
from __future__ import annotations

INCOME_TYPES = frozenset({"INCOME", "RECEIPT"})
EXPENSE_TYPES = frozenset({"EXPENSE", "PAYMENT"})
CASH_MOVEMENT_ONLY_TYPES = frozenset({"OWNER_WITHDRAWAL", "LOAN_PAYMENT"})
KNOWN_TYPES = INCOME_TYPES | EXPENSE_TYPES | CASH_MOVEMENT_ONLY_TYPES
OUTFLOW_TYPES = EXPENSE_TYPES | CASH_MOVEMENT_ONLY_TYPES
INACTIVE_STATUSES = frozenset({"VOID", "CANCELLED", "DELETED"})


def normalize_transaction_type(value) -> str:
    return str(value or "").strip().upper()


def normalize_status(value) -> str:
    return str(value or "RECORDED").strip().upper()


def is_active(record) -> bool:
    """Whether the row remains economically active in reporting."""
    return normalize_status(getattr(record, "status", None)) not in INACTIVE_STATUSES


def _type_of(record) -> str:
    return normalize_transaction_type(getattr(record, "transaction_type", None))


def is_income(record) -> bool:
    return is_active(record) and _type_of(record) in INCOME_TYPES


def is_expense(record) -> bool:
    return is_active(record) and _type_of(record) in EXPENSE_TYPES


def is_cash_movement_only(record) -> bool:
    return is_active(record) and _type_of(record) in CASH_MOVEMENT_ONLY_TYPES


def is_outflow(record) -> bool:
    return is_active(record) and _type_of(record) in OUTFLOW_TYPES


def is_known_type(record) -> bool:
    """Whether the row's transaction type is governed and reportable."""
    return _type_of(record) in KNOWN_TYPES
