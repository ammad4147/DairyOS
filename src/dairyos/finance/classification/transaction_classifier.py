"""Canonical financial transaction-type classification (Phase 1, 2026-08-14).

Single source of truth for what a ``FinancialTransaction.transaction_type``
means to reporting, so every financial surface agrees.

The operator UI offers six transaction types
(``src/DairyOS.Web/src/App.tsx``'s ``entryConfigs.finance``): INCOME,
EXPENSE, RECEIPT, PAYMENT, OWNER_WITHDRAWAL, LOAN_PAYMENT. Before this
module existed, every financial report matched only the literal strings
``"INCOME"`` and ``"EXPENSE"`` — so a transaction recorded as any of the
other four was persisted, counted in ``transaction_count``, and then
contributed nothing to income, expenses or net movement. The books
silently failed to balance.

The classification below was taken as an explicit decision by the farm
owner on 2026-08-14:

* **Income-affecting** (money in, and it is farm revenue): INCOME, RECEIPT.
* **Expense-affecting** (money out, and it is a cost of running the farm):
  EXPENSE, PAYMENT.
* **Cash movement only** (real money out, but NOT a farm expense):
  OWNER_WITHDRAWAL, LOAN_PAYMENT.

That third bucket is the one that matters most. An owner drawing is a
distribution of profit, not a cost of producing milk; a loan repayment is
principally the settlement of a liability, not an operating cost (only the
interest portion would be, and DairyOS does not split the two today — see
the caveat below). Counting either as an expense would inflate cost per
litre — the exact figure AA-014 exists to compute honestly.

**Known limitation, deliberately not solved here:** a LOAN_PAYMENT that
mixes principal and interest is treated wholly as a cash movement, so the
interest portion is currently excluded from expenses. That understates
cost per litre by the interest amount. Splitting it needs either a
separate interest category or two entries per payment, which is a
data-entry design decision for the operator, not something to infer.
AA-014 §6 already lists financing as an OPEX group for the manual
calculator, so the cost-of-production figure there can capture interest
independently of this ledger.
"""
from __future__ import annotations

INCOME_TYPES = frozenset({"INCOME", "RECEIPT"})
EXPENSE_TYPES = frozenset({"EXPENSE", "PAYMENT"})
CASH_MOVEMENT_ONLY_TYPES = frozenset({"OWNER_WITHDRAWAL", "LOAN_PAYMENT"})

#: Every type the operator UI can submit. Kept in sync with
#: ``reference_data.GOVERNED["financial_transaction_types"]`` by
#: ``tests/api/test_finance_transaction_integrity.py``.
KNOWN_TYPES = INCOME_TYPES | EXPENSE_TYPES | CASH_MOVEMENT_ONLY_TYPES

#: Types that move money out of the farm's cash position, whether or not
#: they are an operating expense.
OUTFLOW_TYPES = EXPENSE_TYPES | CASH_MOVEMENT_ONLY_TYPES


def normalize_transaction_type(value) -> str:
    return str(value or "").strip().upper()


def _type_of(record) -> str:
    return normalize_transaction_type(getattr(record, "transaction_type", None))


def is_income(record) -> bool:
    """Money in that counts as farm revenue."""
    return _type_of(record) in INCOME_TYPES


def is_expense(record) -> bool:
    """Money out that counts as a cost of running the farm.

    Deliberately excludes owner withdrawals and loan repayments — see the
    module docstring.
    """
    return _type_of(record) in EXPENSE_TYPES


def is_cash_movement_only(record) -> bool:
    """Real money out that is NOT a farm expense (drawings, loan principal)."""
    return _type_of(record) in CASH_MOVEMENT_ONLY_TYPES


def is_outflow(record) -> bool:
    """Any movement of money out of the farm, expense or not."""
    return _type_of(record) in OUTFLOW_TYPES


def is_known_type(record) -> bool:
    """Whether this record's type is one DairyOS knows how to classify.

    An unknown type is not silently bucketed anywhere. Callers that report
    totals should surface the count of unclassified records rather than
    let them vanish — absence of data must never render as good news.
    """
    return _type_of(record) in KNOWN_TYPES
