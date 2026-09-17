"""Finance reporting: management, reconciliation and audit-support reports.

Authority: ``FinancialTransaction`` read through the canonical
``transaction_classifier`` (active / VOID, revenue / expense / cash-only) and
``finance.ledger_semantics`` (labels and settlement position).

Accounting boundary. DairyOS Finance is a single-entry, status-settled
transaction ledger. These reports therefore present recorded revenue and
recorded expenses by transaction date, receivable and payable positions, and
settlements. They do not present a Trial Balance, Balance Sheet, statutory
Profit and Loss, Cash Flow Statement, depreciation or accruals, because the
ledger does not hold the information those statements require.
"Revenue less Expenses" is an arithmetic management position, not profit.
"""

from __future__ import annotations

import re
from collections import OrderedDict, defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func

from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.milk_disposition import MilkDisposition
from dairyos.data.models.semen_inventory import SemenLot
from dairyos.finance import ledger_semantics as semantics
from dairyos.finance.classification import transaction_classifier as classifier
from dairyos.finance.opex_attribution import is_operating_expense
from dairyos.finance.opex_period_attribution import attribute_opex_for_period
from dairyos.reporting.context import ZERO, ReportContext, clean_text, money, ratio, to_date, upper
from dairyos.reporting.definitions import (
    Column,
    Filter,
    Metric,
    ReconciliationCheck,
    ReportDefinition,
    ReportResult,
    Section,
)
from dairyos.reporting.engine import column_set
from dairyos.reporting.periods import format_date, month_sequence, quarter_of, quarter_sequence

AREA = "finance"
PERMISSION = "finance.view"
AUTHORITY = "Finance ledger (FinancialTransaction) via the canonical transaction classifier"

_AUDIT_LINE = re.compile(r"^(STATUS_TRANSITION_AT=|COP_ATTRIBUTION_CHANGE_AT=|VOIDED_AT=)")
_VOID_TRANSITION = re.compile(
    r"^STATUS_TRANSITION_AT=(?P<at>\S+)\s+FROM=(?P<from>\w+)\s+TO=VOID(?:\s+REASON=(?P<reason>.*))?$"
)
_VOIDED_AT = re.compile(r"^VOIDED_AT=(?P<at>\S+)(?:\s+REASON=(?P<reason>.*))?$")


# ---------------------------------------------------------------------------
# Ledger access
# ---------------------------------------------------------------------------

def ledger_rows(ctx: ReportContext, start: date | None, end: date | None) -> list[FinancialTransaction]:
    """Ledger rows whose transaction date lies in the inclusive period.

    Filtering happens in SQL. ``transaction_date`` is a DateTime whose date
    part is the operator-selected farm date, so the inclusive upper bound is
    expressed as "< the day after To Date".
    """
    query = ctx.session.query(FinancialTransaction)
    if start is not None:
        query = query.filter(FinancialTransaction.transaction_date >= datetime.combine(start, time.min))
    if end is not None:
        query = query.filter(
            FinancialTransaction.transaction_date < datetime.combine(end + timedelta(days=1), time.min)
        )
    return query.order_by(FinancialTransaction.transaction_date, FinancialTransaction.id).all()


def _sql_active_total(ctx: ReportContext, start: date, end: date, types: frozenset[str]) -> Decimal:
    """Independent control total computed by the database, not by Python."""
    value = (
        ctx.session.query(func.coalesce(func.sum(FinancialTransaction.amount), 0))
        .filter(
            FinancialTransaction.transaction_date >= datetime.combine(start, time.min),
            FinancialTransaction.transaction_date < datetime.combine(end + timedelta(days=1), time.min),
            func.upper(func.trim(FinancialTransaction.transaction_type)).in_(sorted(types)),
            func.upper(func.coalesce(FinancialTransaction.status, "RECORDED")).notin_(
                sorted(classifier.INACTIVE_STATUSES)
            ),
        )
        .scalar()
    )
    return money(value)


def split_notes(notes: Any) -> tuple[str | None, list[str]]:
    """Separate operator notes from machine-written lifecycle evidence."""
    operator: list[str] = []
    audit: list[str] = []
    for line in str(notes or "").splitlines():
        text = line.strip()
        if not text:
            continue
        (audit if _AUDIT_LINE.match(text) else operator).append(text)
    return (" ".join(operator) or None), audit


def void_evidence(notes: Any) -> tuple[str | None, str | None, str | None]:
    """Return ``(voided_at, status_before_void, reason)`` from ledger evidence."""
    for line in reversed(split_notes(notes)[1]):
        match = _VOID_TRANSITION.match(line)
        if match:
            return match["at"][:19].replace("T", " "), match["from"], clean_text(match["reason"])
        match = _VOIDED_AT.match(line)
        if match:
            return match["at"][:19].replace("T", " "), None, clean_text(match["reason"])
    return None, None, None


def operational_reference(row: FinancialTransaction) -> str | None:
    """Related operational record, in operator language."""
    if getattr(row, "payroll_record_id", None):
        return f"Payroll record {row.payroll_record_id}"
    if getattr(row, "milk_sale_id", None):
        return f"Milk sale {row.milk_sale_id}"
    if upper(row.category) == "MILK_SALES" and semantics.nature(row) == semantics.NATURE_REVENUE:
        return f"Milk sale FIN-{row.id}"
    if getattr(row, "animal_id", None):
        return f"Animal {row.animal_id}"
    if getattr(row, "feed_record_id", None):
        return f"Feed record {row.feed_record_id}"
    return None


def transaction_row(row: FinancialTransaction) -> dict[str, Any]:
    operator_notes, audit = split_notes(row.notes)
    amount = money(row.amount)
    active = classifier.is_active(row)
    outstanding = amount if active and semantics.is_outstanding(row) else ZERO
    master = clean_text(row.master_category)
    return {
        "transaction_date": to_date(row.transaction_date),
        "transaction_no": f"FIN-{row.id}",
        "nature": semantics.NATURE_LABELS[semantics.nature(row)],
        "category_group": semantics.group_label(row),
        "category": semantics.category_label(row),
        "description": clean_text(row.custom_specification) or operator_notes,
        "counterparty": clean_text(row.counterparty),
        "reference": clean_text(row.reference),
        "quantity": row.quantity,
        "unit": clean_text(row.unit),
        "unit_rate": float(row.unit_rate) if row.unit_rate is not None else None,
        "amount": amount,
        "active_amount": amount if active else ZERO,
        "settled_amount": (amount - outstanding) if active else ZERO,
        "outstanding_amount": outstanding,
        "status": upper(row.status) or "RECORDED",
        "settlement": semantics.settlement_label(row),
        "payment_method": clean_text(row.payment_method),
        "due_date": row.due_date,
        "settled_date": row.settled_date,
        "related_record": operational_reference(row),
        "currency": clean_text(row.currency) or "PKR",
        "notes": operator_notes,
        "cost_treatment": (
            None if semantics.nature(row) != semantics.NATURE_EXPENSE
            else "Feed (TMR authority)" if upper(master) == "FEED"
            else "OPEX" if is_operating_expense(row) else "Non-OPEX"
        ),
        "lifecycle_evidence": " | ".join(audit) or None,
    }


LEDGER_COLUMNS = column_set(
    Column("transaction_date", "Date", "date", "Transaction"),
    Column("transaction_no", "Transaction No.", "text", "Transaction"),
    Column("nature", "Type", "text", "Transaction"),
    Column("category_group", "Category Group", "text", "Classification"),
    Column("category", "Category / Item", "text", "Classification"),
    Column("cost_treatment", "Cost Treatment", "text", "Classification", "optional"),
    Column("description", "Description", "text", "Transaction", "optional"),
    Column("counterparty", "Counterparty", "text", "Parties"),
    Column("reference", "Reference", "text", "Parties", "optional"),
    Column("quantity", "Quantity", "number", "Quantity & Rate", "optional"),
    Column("unit", "Unit", "text", "Quantity & Rate", "optional"),
    Column("unit_rate", "Rate (PKR)", "rate", "Quantity & Rate", "optional"),
    Column("amount", "Amount (PKR)", "money", "Amounts"),
    Column("active_amount", "Active Amount (PKR)", "money", "Amounts", "optional", total=True),
    Column("settled_amount", "Settled (PKR)", "money", "Amounts", "optional", total=True),
    Column("outstanding_amount", "Outstanding (PKR)", "money", "Amounts", "optional", total=True),
    Column("status", "Status", "status", "Settlement"),
    Column("payment_method", "Payment Method", "text", "Settlement", "optional"),
    Column("due_date", "Due Date", "date", "Settlement", "optional"),
    Column("settled_date", "Settled Date", "date", "Settlement", "optional"),
    Column("related_record", "Related Record", "text", "Audit", "optional"),
    Column("notes", "Notes", "text", "Audit", "optional"),
    Column("lifecycle_evidence", "Status Change Evidence", "text", "Audit", "advanced"),
)

NATURE_FILTER = Filter(
    "nature", "Transaction Type",
    options=(
        ("REVENUE", "Revenue"), ("EXPENSE", "Expense"),
        ("CAPITAL_INFLOW", "Capital Inflow"), ("CASH_MOVEMENT", "Cash Movement"),
    ),
)
STATUS_FILTER = Filter(
    "status", "Status",
    options=tuple((s, s.title()) for s in ("RECORDED", "RECEIVED", "RECEIVABLE", "PAID", "PAYABLE", "VOID")),
)


def _ledger_totals(rows: list[dict[str, Any]], label: str = "Total (active transactions)") -> dict[str, Any]:
    return {
        "_label": label,
        "active_amount": sum((r["active_amount"] for r in rows), ZERO),
        "settled_amount": sum((r["settled_amount"] for r in rows), ZERO),
        "outstanding_amount": sum((r["outstanding_amount"] for r in rows), ZERO),
        "amount": sum((r["active_amount"] for r in rows), ZERO),
    }


# ---------------------------------------------------------------------------
# Transaction ledger
# ---------------------------------------------------------------------------

def build_ledger(ctx: ReportContext) -> ReportResult:
    wanted_nature = ctx.filter("nature")
    wanted_status = ctx.filter("status")
    group = ctx.filter("category_group")
    category = ctx.filter("category")
    party = ctx.filter("counterparty")
    include_void = ctx.flag("include_void", True)

    rows = []
    for record in ledger_rows(ctx, ctx.period.start, ctx.period.end):
        if wanted_nature and semantics.nature(record) != wanted_nature:
            continue
        if wanted_status and upper(record.status or "RECORDED") != wanted_status:
            continue
        if not include_void and semantics.is_void(record):
            continue
        if group and semantics.group_label(record) != group:
            continue
        if category and semantics.category_label(record) != category:
            continue
        if party and party.lower() not in str(record.counterparty or "").lower():
            continue
        rows.append(transaction_row(record))

    void_rows = [r for r in rows if r["status"] == "VOID"]
    notes = []
    if void_rows:
        notes.append(
            f"{len(void_rows)} VOID transaction(s) are listed for audit visibility. "
            "VOID amounts are excluded from every total."
        )
    return ReportResult(
        sections=[Section("ledger", "Transactions", LEDGER_COLUMNS, rows, _ledger_totals(rows), primary=True)],
        summary=[
            Metric("transactions", "Transactions Listed", len(rows), "integer"),
            Metric("active_total", "Active Amount", sum((r["active_amount"] for r in rows), ZERO), "money"),
            Metric("void_count", "VOID Transactions", len(void_rows), "integer"),
        ],
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Revenue / Expense reconciliation
# ---------------------------------------------------------------------------

REVENUE_COLUMNS = column_set(
    Column("group", "Revenue Category"),
    Column("category", "Revenue Item"),
    Column("transactions", "Transactions", "integer", total=True),
    Column("quantity", "Quantity", "number"),
    Column("unit", "Unit"),
    Column("gross", "Gross Amount (PKR)", "money", total=True),
    Column("received", "Received (PKR)", "money", total=True),
    Column("outstanding", "Outstanding (PKR)", "money", total=True),
    Column("share", "% of Revenue", "percent"),
)

EXPENSE_COLUMNS = column_set(
    Column("master", "Cost Class"),
    Column("group", "Expense Category"),
    Column("transactions", "Transactions", "integer", total=True),
    Column("amount", "Amount (PKR)", "money", total=True),
    Column("paid", "Paid (PKR)", "money", total=True),
    Column("payable", "Payable (PKR)", "money", total=True),
    Column("share", "% of Total", "percent"),
)

EXPENSE_ITEM_COLUMNS = column_set(
    Column("group", "Expense Category"),
    Column("item", "Expense Item"),
    Column("transactions", "Transactions", "integer", total=True),
    Column("amount", "Amount (PKR)", "money", total=True),
    Column("share", "% of Total", "percent"),
)

POSITION_COLUMNS = column_set(
    Column("line", "Line"),
    Column("amount", "Amount (PKR)", "money"),
    Column("basis", "Basis"),
)


def _share(part: Decimal, whole: Decimal) -> float | None:
    return ratio(part * 100, whole) if whole else None


def _drill(ctx: ReportContext, label: str, **filters: str) -> dict[str, Any]:
    return {"report_id": "fin-transaction-ledger", "label": label, "filters": filters,
            "period": {"mode": "CUSTOM", "start_date": ctx.period.start.isoformat(),
                       "end_date": ctx.period.end.isoformat()}}


def revenue_section(ctx: ReportContext, records: list[FinancialTransaction]) -> tuple[Section, Decimal]:
    buckets: "OrderedDict[tuple[str, str], dict[str, Any]]" = OrderedDict()
    for record in records:
        if not classifier.is_income(record):
            continue
        group, _code, label = semantics.revenue_category(record)
        bucket = buckets.setdefault((group, label), {
            "group": group, "category": label, "transactions": 0, "quantity": None, "unit": None,
            "gross": ZERO, "received": ZERO, "outstanding": ZERO,
        })
        amount = money(record.amount)
        bucket["transactions"] += 1
        bucket["gross"] += amount
        if semantics.is_outstanding(record):
            bucket["outstanding"] += amount
        else:
            bucket["received"] += amount
        if record.quantity is not None:
            bucket["quantity"] = round((bucket["quantity"] or 0) + float(record.quantity), 3)
            bucket["unit"] = clean_text(record.unit) or bucket["unit"]

    order = {name: index for index, name in enumerate(semantics.REVENUE_GROUP_ORDER)}
    rows = sorted(buckets.values(), key=lambda r: (order.get(r["group"], 99), r["category"]))
    total = sum((r["gross"] for r in rows), ZERO)
    for row in rows:
        row["share"] = _share(row["gross"], total)
        row["_drill"] = _drill(ctx, row["category"], nature="REVENUE", category=row["category"])
    totals = {
        "_label": "Total Revenue",
        "transactions": sum(r["transactions"] for r in rows),
        "gross": total,
        "received": sum((r["received"] for r in rows), ZERO),
        "outstanding": sum((r["outstanding"] for r in rows), ZERO),
        "share": 100.0 if total else None,
    }
    section = Section(
        "revenue", "Revenue", REVENUE_COLUMNS, rows, totals,
        note="Recorded revenue by transaction date. VOID transactions are excluded.",
        empty_message="No revenue was recorded in this period.",
    )
    return section, total


def expense_sections(ctx: ReportContext, records: list[FinancialTransaction]) -> tuple[Section, Section, Decimal]:
    groups: "OrderedDict[tuple[str, str], dict[str, Any]]" = OrderedDict()
    items: "OrderedDict[tuple[str, str], dict[str, Any]]" = OrderedDict()
    for record in records:
        if not classifier.is_expense(record):
            continue
        master, _code, group, item = semantics.expense_category(record)
        amount = money(record.amount)
        bucket = groups.setdefault((master, group), {
            "master": master, "group": group, "transactions": 0,
            "amount": ZERO, "paid": ZERO, "payable": ZERO,
        })
        bucket["transactions"] += 1
        bucket["amount"] += amount
        bucket["payable" if semantics.is_outstanding(record) else "paid"] += amount
        line = items.setdefault((group, item), {"group": group, "item": item, "transactions": 0, "amount": ZERO})
        line["transactions"] += 1
        line["amount"] += amount

    master_order = {"Feed": 0, "OPEX": 1, "Non-OPEX": 2, "Legacy": 3}
    group_rows = sorted(groups.values(), key=lambda r: (master_order.get(r["master"], 9), -r["amount"], r["group"]))
    item_rows = sorted(items.values(), key=lambda r: (r["group"], -r["amount"], r["item"]))
    total = sum((r["amount"] for r in group_rows), ZERO)
    for row in group_rows:
        row["share"] = _share(row["amount"], total)
        row["_drill"] = _drill(ctx, row["group"], nature="EXPENSE", category_group=row["group"])
    for row in item_rows:
        row["share"] = _share(row["amount"], total)
        row["_drill"] = _drill(ctx, row["item"], nature="EXPENSE", category=row["item"])

    group_section = Section(
        "expenses", "Expenses", EXPENSE_COLUMNS, group_rows,
        {
            "_label": "Total Expenses",
            "transactions": sum(r["transactions"] for r in group_rows),
            "amount": total,
            "paid": sum((r["paid"] for r in group_rows), ZERO),
            "payable": sum((r["payable"] for r in group_rows), ZERO),
            "share": 100.0 if total else None,
        },
        note="Recorded expenses by transaction date, using the governed Finance expense taxonomy. "
             "VOID transactions are excluded.",
        empty_message="No expenses were recorded in this period.",
    )
    item_section = Section(
        "expense-items", "Expenses by Item", EXPENSE_ITEM_COLUMNS, item_rows,
        {"_label": "Total Expenses", "transactions": sum(r["transactions"] for r in item_rows),
         "amount": total, "share": 100.0 if total else None},
        empty_message="No expenses were recorded in this period.",
    )
    return group_section, item_section, total


def _void_metrics(records: list[FinancialTransaction]) -> tuple[int, Decimal]:
    void = [r for r in records if semantics.is_void(r)]
    return len(void), sum((money(r.amount) for r in void), ZERO)


def build_reconciliation(ctx: ReportContext) -> ReportResult:
    """Revenue, Expense, or combined Revenue and Expense reconciliation."""
    scope = ctx.preset.get("scope", "BOTH")
    start, end = ctx.period.start, ctx.period.end
    records = ledger_rows(ctx, start, end)

    sections: list[Section] = []
    summary: list[Metric] = []
    checks: list[ReconciliationCheck] = []
    revenue_total = expense_total = ZERO

    if scope in {"BOTH", "REVENUE"}:
        section, revenue_total = revenue_section(ctx, records)
        section.primary = scope in {"REVENUE", "BOTH"}
        sections.append(section)
        detail = sum((money(r.amount) for r in records if classifier.is_income(r)), ZERO)
        checks.append(ReconciliationCheck("Revenue categories equal transaction detail", detail, revenue_total))
        checks.append(ReconciliationCheck(
            "Revenue equals database control total",
            _sql_active_total(ctx, start, end, classifier.INCOME_TYPES), revenue_total,
        ))
        summary.append(Metric("total_revenue", "Total Revenue", revenue_total, "money"))
        summary.append(Metric("receivable", "Of Which Outstanding", section.totals["outstanding"], "money"))

    if scope in {"BOTH", "EXPENSE"}:
        group_section, item_section, expense_total = expense_sections(ctx, records)
        group_section.primary = scope == "EXPENSE"
        sections.append(group_section)
        if scope == "EXPENSE":
            sections.append(item_section)
        detail = sum((money(r.amount) for r in records if classifier.is_expense(r)), ZERO)
        checks.append(ReconciliationCheck("Expense categories equal transaction detail", detail, expense_total))
        checks.append(ReconciliationCheck(
            "Expenses equal database control total",
            _sql_active_total(ctx, start, end, classifier.EXPENSE_TYPES), expense_total,
        ))
        summary.append(Metric("total_expenses", "Total Expenses", expense_total, "money"))
        summary.append(Metric("payable", "Of Which Payable", group_section.totals["payable"], "money"))

    void_count, void_amount = _void_metrics(records)
    notes = [
        "Basis: transactions recorded in the Finance ledger, by transaction date, inclusive of both period dates.",
    ]
    if void_count:
        notes.append(
            f"{void_count} VOID transaction(s) totalling PKR {void_amount:,.2f} fall in this period. "
            "They are excluded from all figures and remain listed in VOID Transaction History."
        )

    if scope == "BOTH":
        capital = sum((money(r.amount) for r in records if classifier.is_cash_inflow_only(r)), ZERO)
        movements = sum((money(r.amount) for r in records if classifier.is_cash_movement_only(r)), ZERO)
        position_rows = [
            {"line": "Total Revenue", "amount": revenue_total, "basis": "Recorded revenue, VOID excluded"},
            {"line": "Total Expenses", "amount": expense_total, "basis": "Recorded expenses incl. Feed, OPEX and Non-OPEX, VOID excluded"},
            {"line": "Revenue less Expenses", "amount": revenue_total - expense_total,
             "basis": "Arithmetic management position. Not profit: no depreciation, accruals, stock or tax.",
             "_emphasis": "total"},
            {"line": "Memo: Capital Inflows (owner investment)", "amount": capital,
             "basis": "Not revenue. Shown for completeness of the ledger."},
            {"line": "Memo: Cash Movements (owner draw, loan payment)", "amount": movements,
             "basis": "Not expenses. Shown for completeness of the ledger."},
        ]
        sections.append(Section("position", "Management Position", POSITION_COLUMNS, position_rows))
        summary.append(Metric("position", "Revenue less Expenses", revenue_total - expense_total, "money",
                              "Arithmetic position, not profit"))
        active_total = sum((money(r.amount) for r in records if classifier.is_active(r)), ZERO)
        checks.append(ReconciliationCheck(
            "All active ledger value is classified", active_total,
            revenue_total + expense_total + capital + movements
            + sum((money(r.amount) for r in records
                   if classifier.is_active(r) and not classifier.is_known_type(r)), ZERO),
        ))
        unknown = [r for r in records if classifier.is_active(r) and not classifier.is_known_type(r)]
        if unknown:
            notes.append(
                f"{len(unknown)} active transaction(s) carry an ungoverned transaction type and are not "
                "included in revenue or expenses. Review them in the Transaction Ledger."
            )

    summary.append(Metric("void", "VOID Excluded", void_amount, "money", f"{void_count} transaction(s)"))
    return ReportResult(sections, summary, notes, checks)


# ---------------------------------------------------------------------------
# Periodic summary and daily activity
# ---------------------------------------------------------------------------

PERIODIC_COLUMNS = column_set(
    Column("period", "Period"),
    Column("from_date", "From", "date"),
    Column("to_date", "To", "date"),
    Column("transactions", "Active Transactions", "integer", total=True),
    Column("revenue", "Revenue (PKR)", "money", total=True),
    Column("expenses", "Expenses (PKR)", "money", total=True),
    Column("position", "Revenue less Expenses (PKR)", "money", total=True),
    Column("feed", "Feed (PKR)", "money", "Expense Classes", "optional", total=True),
    Column("opex", "OPEX (PKR)", "money", "Expense Classes", "optional", total=True),
    Column("non_opex", "Non-OPEX (PKR)", "money", "Expense Classes", "optional", total=True),
    Column("capital_in", "Capital Inflows (PKR)", "money", "Cash Only", "optional", total=True),
    Column("cash_out", "Cash Movements (PKR)", "money", "Cash Only", "optional", total=True),
)


def _flow_bucket() -> dict[str, Any]:
    return {"transactions": 0, "revenue": ZERO, "expenses": ZERO, "feed": ZERO, "opex": ZERO,
            "non_opex": ZERO, "capital_in": ZERO, "cash_out": ZERO}


def _add_flow(bucket: dict[str, Any], record: FinancialTransaction) -> None:
    if not classifier.is_active(record):
        return
    amount = money(record.amount)
    bucket["transactions"] += 1
    if classifier.is_income(record):
        bucket["revenue"] += amount
    elif classifier.is_expense(record):
        bucket["expenses"] += amount
        if upper(record.master_category) == "FEED" or (
            not record.master_category and upper(record.category) == "FEED"
        ):
            bucket["feed"] += amount
        elif is_operating_expense(record):
            bucket["opex"] += amount
        else:
            bucket["non_opex"] += amount
    elif classifier.is_cash_inflow_only(record):
        bucket["capital_in"] += amount
    elif classifier.is_cash_movement_only(record):
        bucket["cash_out"] += amount


def _flow_totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Any] = {"_label": "Total"}
    for key in ("transactions", "revenue", "expenses", "position", "feed", "opex", "non_opex", "capital_in", "cash_out"):
        totals[key] = sum((r[key] for r in rows), 0 if key == "transactions" else ZERO)
    return totals


def build_periodic_summary(ctx: ReportContext) -> ReportResult:
    start, end = ctx.period.start, ctx.period.end
    granularity = ctx.filter("granularity") or "MONTH"
    spans = quarter_sequence(start, end) if granularity == "QUARTER" else month_sequence(start, end)
    records = ledger_rows(ctx, start, end)

    rows = []
    for first, last in spans:
        bucket = _flow_bucket()
        for record in records:
            day = to_date(record.transaction_date)
            if day is not None and first <= day <= last:
                _add_flow(bucket, record)
        label = f"Q{quarter_of(first)} {first.year}" if granularity == "QUARTER" else first.strftime("%B %Y")
        bucket.update({"period": label, "from_date": first, "to_date": last,
                       "position": bucket["revenue"] - bucket["expenses"]})
        rows.append(bucket)

    totals = _flow_totals(rows)
    return ReportResult(
        sections=[Section("periods", "Financial Summary by Period", PERIODIC_COLUMNS, rows, totals, primary=True,
                          note="A first or last period is partial when the selected range does not start or end on its boundary.")],
        summary=[
            Metric("revenue", "Total Revenue", totals["revenue"], "money"),
            Metric("expenses", "Total Expenses", totals["expenses"], "money"),
            Metric("position", "Revenue less Expenses", totals["position"], "money", "Arithmetic position, not profit"),
        ],
        reconciliation=[
            ReconciliationCheck("Period rows equal revenue control total",
                                _sql_active_total(ctx, start, end, classifier.INCOME_TYPES), totals["revenue"]),
            ReconciliationCheck("Period rows equal expense control total",
                                _sql_active_total(ctx, start, end, classifier.EXPENSE_TYPES), totals["expenses"]),
        ],
    )


DAILY_COLUMNS = column_set(
    Column("date", "Date", "date"),
    Column("transactions", "Active Transactions", "integer", total=True),
    Column("revenue", "Revenue (PKR)", "money", total=True),
    Column("expenses", "Expenses (PKR)", "money", total=True),
    Column("position", "Revenue less Expenses (PKR)", "money", total=True),
    Column("capital_in", "Capital Inflows (PKR)", "money", "Cash Only", "optional", total=True),
    Column("cash_out", "Cash Movements (PKR)", "money", "Cash Only", "optional", total=True),
    Column("feed", "Feed (PKR)", "money", "Expense Classes", "optional", total=True),
    Column("opex", "OPEX (PKR)", "money", "Expense Classes", "optional", total=True),
    Column("non_opex", "Non-OPEX (PKR)", "money", "Expense Classes", "optional", total=True),
)


def build_daily_activity(ctx: ReportContext) -> ReportResult:
    days: dict[date, dict[str, Any]] = defaultdict(_flow_bucket)
    for record in ledger_rows(ctx, ctx.period.start, ctx.period.end):
        day = to_date(record.transaction_date)
        if day is not None and classifier.is_active(record):
            _add_flow(days[day], record)
    rows = []
    for day in sorted(days):
        bucket = days[day]
        bucket.update({"date": day, "position": bucket["revenue"] - bucket["expenses"]})
        bucket["_drill"] = {"report_id": "fin-transaction-ledger", "label": format_date(day), "filters": {},
                            "period": {"mode": "CUSTOM", "start_date": day.isoformat(), "end_date": day.isoformat()}}
        rows.append(bucket)
    totals = _flow_totals(rows)
    return ReportResult(
        sections=[Section("days", "Daily Financial Activity", DAILY_COLUMNS, rows, totals, primary=True,
                          note="Only days with at least one active transaction are listed.")],
        summary=[
            Metric("days", "Days with Activity", len(rows), "integer"),
            Metric("revenue", "Total Revenue", totals["revenue"], "money"),
            Metric("expenses", "Total Expenses", totals["expenses"], "money"),
        ],
    )


# ---------------------------------------------------------------------------
# Receivables, payables, settlements
# ---------------------------------------------------------------------------

POSITION_DETAIL_COLUMNS = column_set(
    Column("party", "Party", "text", "Party"),
    Column("transaction_no", "Transaction No.", "text", "Transaction"),
    Column("reference", "Reference", "text", "Transaction", "optional"),
    Column("category", "Category / Item", "text", "Transaction"),
    Column("transaction_date", "Transaction Date", "date", "Dates"),
    Column("due_date", "Due Date", "date", "Dates"),
    Column("original_amount", "Original Amount (PKR)", "money", "Amounts", total=True),
    Column("settled_amount", "Settled (PKR)", "money", "Amounts", total=True),
    Column("outstanding_amount", "Outstanding (PKR)", "money", "Amounts", total=True),
    Column("days_outstanding", "Days Outstanding", "days", "Ageing"),
    Column("days_overdue", "Days Overdue", "days", "Ageing"),
    Column("age_bucket", "Ageing", "text", "Ageing"),
    Column("status", "Status at Date", "status", "Ageing"),
    Column("current_status", "Current Status", "status", "Ageing", "optional"),
    Column("related_record", "Related Record", "text", "Transaction", "optional"),
)

PARTY_COLUMNS = column_set(
    Column("party", "Party"),
    Column("transactions", "Transactions", "integer", total=True),
    Column("outstanding_amount", "Outstanding (PKR)", "money", total=True),
    Column("overdue_amount", "Of Which Overdue (PKR)", "money", total=True),
    Column("oldest_days", "Oldest (Days)", "days"),
)

AGE_COLUMNS = column_set(
    Column("age_bucket", "Ageing Bucket"),
    Column("transactions", "Transactions", "integer", total=True),
    Column("outstanding_amount", "Outstanding (PKR)", "money", total=True),
)

AGE_ORDER = ("Not yet due", "1 to 30 days overdue", "31 to 60 days overdue",
             "61 to 90 days overdue", "Over 90 days overdue", "No due date")


def _age_bucket(due: date | None, as_of: date) -> tuple[str, int | None]:
    """Same bucket boundaries as the Finance ageing authority."""
    if due is None:
        return "No due date", None
    overdue = (as_of - due).days
    if overdue <= 0:
        return "Not yet due", 0
    if overdue <= 30:
        return "1 to 30 days overdue", overdue
    if overdue <= 60:
        return "31 to 60 days overdue", overdue
    if overdue <= 90:
        return "61 to 90 days overdue", overdue
    return "Over 90 days overdue", overdue


def build_open_position(ctx: ReportContext) -> ReportResult:
    """Receivables or payables outstanding as of a date.

    Finance settles in full and stamps ``settled_date``. A row was therefore
    outstanding on date D when it was dated on or before D and either is
    still open today, or was settled after D. VOID rows hold no position.
    """
    side = ctx.preset["side"]  # RECEIVABLE | PAYABLE
    open_status, settled_status = ("RECEIVABLE", "RECEIVED") if side == "RECEIVABLE" else ("PAYABLE", "PAID")
    wanted = classifier.is_income if side == "RECEIVABLE" else classifier.is_expense
    as_of = ctx.period.as_of
    party_filter = ctx.filter("counterparty")
    default_party = "Unspecified Buyer" if side == "RECEIVABLE" else "Unspecified Supplier"

    rows = []
    for record in ledger_rows(ctx, None, as_of):
        if not wanted(record):
            continue
        status = upper(record.status or "RECORDED")
        if status == open_status:
            pass
        elif status == settled_status and record.settled_date is not None and record.settled_date > as_of:
            pass
        else:
            continue
        party = clean_text(record.counterparty) or default_party
        if party_filter and party_filter.lower() not in party.lower():
            continue
        amount = money(record.amount)
        day = to_date(record.transaction_date)
        bucket, overdue = _age_bucket(record.due_date, as_of)
        rows.append({
            "party": party,
            "transaction_no": f"FIN-{record.id}",
            "reference": clean_text(record.reference),
            "category": semantics.category_label(record),
            "transaction_date": day,
            "due_date": record.due_date,
            "original_amount": amount,
            "settled_amount": ZERO,
            "outstanding_amount": amount,
            "days_outstanding": (as_of - day).days if day else None,
            "days_overdue": overdue,
            "age_bucket": bucket,
            "status": open_status,
            "current_status": status,
            "related_record": operational_reference(record),
        })

    total = sum((r["outstanding_amount"] for r in rows), ZERO)
    overdue_total = sum((r["outstanding_amount"] for r in rows if (r["days_overdue"] or 0) > 0), ZERO)

    parties: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = parties.setdefault(row["party"], {"party": row["party"], "transactions": 0,
                                                   "outstanding_amount": ZERO, "overdue_amount": ZERO, "oldest_days": 0})
        bucket["transactions"] += 1
        bucket["outstanding_amount"] += row["outstanding_amount"]
        if (row["days_overdue"] or 0) > 0:
            bucket["overdue_amount"] += row["outstanding_amount"]
        bucket["oldest_days"] = max(bucket["oldest_days"], row["days_outstanding"] or 0)
    party_rows = sorted(parties.values(), key=lambda r: (-r["outstanding_amount"], r["party"]))

    ages = {name: {"age_bucket": name, "transactions": 0, "outstanding_amount": ZERO} for name in AGE_ORDER}
    for row in rows:
        ages[row["age_bucket"]]["transactions"] += 1
        ages[row["age_bucket"]]["outstanding_amount"] += row["outstanding_amount"]

    title = "Receivables" if side == "RECEIVABLE" else "Payables"
    return ReportResult(
        sections=[
            Section("detail", f"Outstanding {title}", POSITION_DETAIL_COLUMNS, rows,
                    {"_label": f"Total {title}", "original_amount": total, "settled_amount": ZERO,
                     "outstanding_amount": total}, primary=True),
            Section("parties", f"{title} by Party", PARTY_COLUMNS, party_rows,
                    {"_label": "Total", "transactions": len(rows), "outstanding_amount": total,
                     "overdue_amount": overdue_total}),
            Section("ageing", "Ageing Summary", AGE_COLUMNS, [ages[name] for name in AGE_ORDER],
                    {"_label": "Total", "transactions": len(rows), "outstanding_amount": total}),
        ],
        summary=[
            Metric("outstanding", f"Total {title}", total, "money"),
            Metric("overdue", "Of Which Overdue", overdue_total, "money"),
            Metric("count", "Open Transactions", len(rows), "integer"),
            Metric("parties", "Parties", len(party_rows), "integer"),
        ],
        notes=[
            "DairyOS Finance settles a transaction in full. Part-payments against a single transaction are not "
            "recorded, so Settled is PKR 0.00 for every open item and Outstanding equals the original amount.",
        ],
        reconciliation=[
            ReconciliationCheck("Party totals equal detail", total,
                                sum((r["outstanding_amount"] for r in party_rows), ZERO)),
            ReconciliationCheck("Ageing totals equal detail", total,
                                sum((r["outstanding_amount"] for r in ages.values()), ZERO)),
        ],
    )


SETTLEMENT_COLUMNS = column_set(
    Column("settled_date", "Settled Date", "date"),
    Column("direction", "Direction"),
    Column("party", "Party"),
    Column("transaction_no", "Transaction No."),
    Column("category", "Category / Item"),
    Column("transaction_date", "Transaction Date", "date"),
    Column("due_date", "Due Date", "date", "Details", "optional"),
    Column("amount", "Amount Settled (PKR)", "money", total=True),
    Column("days_to_settle", "Days to Settle", "days"),
    Column("payment_method", "Payment Method", "text", "Details", "optional"),
    Column("reference", "Reference", "text", "Details", "optional"),
)


def build_settlements(ctx: ReportContext) -> ReportResult:
    start, end = ctx.period.start, ctx.period.end
    direction_filter = ctx.filter("direction")
    records = (
        ctx.session.query(FinancialTransaction)
        .filter(FinancialTransaction.settled_date >= start, FinancialTransaction.settled_date <= end)
        .order_by(FinancialTransaction.settled_date, FinancialTransaction.id)
        .all()
    )
    rows = []
    for record in records:
        status = upper(record.status)
        if status not in {"RECEIVED", "PAID"} or not classifier.is_active(record):
            continue
        direction = "Received" if status == "RECEIVED" else "Paid"
        if direction_filter and direction.upper() != direction_filter:
            continue
        day = to_date(record.transaction_date)
        rows.append({
            "settled_date": record.settled_date,
            "direction": direction,
            "party": clean_text(record.counterparty),
            "transaction_no": f"FIN-{record.id}",
            "category": semantics.category_label(record),
            "transaction_date": day,
            "due_date": record.due_date,
            "amount": money(record.amount),
            "days_to_settle": (record.settled_date - day).days if day else None,
            "payment_method": clean_text(record.payment_method),
            "reference": clean_text(record.reference),
        })
    received = sum((r["amount"] for r in rows if r["direction"] == "Received"), ZERO)
    paid = sum((r["amount"] for r in rows if r["direction"] == "Paid"), ZERO)
    return ReportResult(
        sections=[Section("settlements", "Settlements", SETTLEMENT_COLUMNS, rows,
                          {"_label": "Total Settled", "amount": received + paid}, primary=True)],
        summary=[
            Metric("received", "Received", received, "money"),
            Metric("paid", "Paid", paid, "money"),
            Metric("count", "Settlements", len(rows), "integer"),
        ],
        notes=[
            "A settlement is a transaction marked Received or Paid, dated by its settled date. "
            "Each transaction settles once and in full.",
        ],
    )


# ---------------------------------------------------------------------------
# VOID history
# ---------------------------------------------------------------------------

VOID_COLUMNS = column_set(
    Column("transaction_date", "Transaction Date", "date"),
    Column("transaction_no", "Transaction No."),
    Column("nature", "Type"),
    Column("category", "Category / Item"),
    Column("counterparty", "Counterparty"),
    Column("amount", "Original Amount (PKR)", "money", total=True),
    Column("status_before", "Status before VOID", "status"),
    Column("voided_at", "Voided At (UTC)", "text"),
    Column("void_reason", "VOID Reason"),
    Column("reference", "Reference", "text", "Details", "optional"),
    Column("related_record", "Related Record", "text", "Details", "optional"),
)


def build_void_history(ctx: ReportContext) -> ReportResult:
    rows = []
    for record in ledger_rows(ctx, ctx.period.start, ctx.period.end):
        if not semantics.is_void(record):
            continue
        voided_at, before, reason = void_evidence(record.notes)
        rows.append({
            "transaction_date": to_date(record.transaction_date),
            "transaction_no": f"FIN-{record.id}",
            "nature": semantics.NATURE_LABELS[semantics.nature(record)],
            "category": semantics.category_label(record),
            "counterparty": clean_text(record.counterparty),
            "amount": money(record.amount),
            "status_before": before,
            "voided_at": voided_at,
            "void_reason": reason,
            "reference": clean_text(record.reference),
            "related_record": operational_reference(record),
        })
    total = sum((r["amount"] for r in rows), ZERO)
    return ReportResult(
        sections=[Section("void", "VOID Transactions", VOID_COLUMNS, rows,
                          {"_label": "Total VOID (excluded from all active figures)", "amount": total}, primary=True)],
        summary=[Metric("count", "VOID Transactions", len(rows), "integer"),
                 Metric("amount", "VOID Amount", total, "money", "Excluded from revenue, expenses, receivables, payables and OPEX")],
        notes=["VOID transactions are retained permanently as audit evidence and never contribute to an active total."],
    )


# ---------------------------------------------------------------------------
# Milk sales and animal sales
# ---------------------------------------------------------------------------

MILK_SALE_COLUMNS = column_set(
    Column("transaction_date", "Date", "date"),
    Column("sale_id", "Sale Reference"),
    Column("buyer", "Buyer"),
    Column("litres", "Litres", "litres", total=True),
    Column("rate", "Rate / Litre (PKR)", "rate"),
    Column("amount", "Amount (PKR)", "money", total=True),
    Column("received", "Received (PKR)", "money", total=True),
    Column("outstanding", "Outstanding (PKR)", "money", total=True),
    Column("status", "Status", "status"),
    Column("milk_record", "Milk Sold Record", "text", "Cross-Module"),
    Column("amount_check", "Qty x Rate less Amount (PKR)", "money", "Cross-Module", "optional"),
    Column("payment_method", "Payment Method", "text", "Details", "optional"),
    Column("due_date", "Due Date", "date", "Details", "optional"),
    Column("settled_date", "Settled Date", "date", "Details", "optional"),
)


def build_milk_sales(ctx: ReportContext) -> ReportResult:
    buyer_filter = ctx.filter("counterparty")
    records = [
        r for r in ledger_rows(ctx, ctx.period.start, ctx.period.end)
        if classifier.is_income(r) and upper(r.category) == "MILK_SALES"
    ]
    sale_ids = [f"FIN-{r.id}" for r in records] + [str(r.milk_sale_id) for r in records if r.milk_sale_id]
    dispositions = {}
    if sale_ids:
        for item in ctx.session.query(MilkDisposition).filter(MilkDisposition.sale_id.in_(sale_ids)).all():
            dispositions[str(item.sale_id)] = item

    rows, mismatches, receipts_on_finance_sales = [], 0, 0
    for record in records:
        if buyer_filter and buyer_filter.lower() not in str(record.counterparty or "").lower():
            continue
        amount = money(record.amount)
        outstanding = amount if semantics.is_outstanding(record) else ZERO
        is_receipt_posting = bool(record.milk_sale_id)
        sale_id = str(record.milk_sale_id) if is_receipt_posting else f"FIN-{record.id}"
        linked = dispositions.get(sale_id)
        if is_receipt_posting:
            milk_record = "Receipt against " + sale_id
            if sale_id.startswith("FIN-"):
                receipts_on_finance_sales += 1
        elif linked is None:
            milk_record, mismatches = "Missing", mismatches + 1
        elif upper(linked.status) == "VOID":
            milk_record, mismatches = "Milk record is VOID", mismatches + 1
        elif (round(float(linked.quantity_litres or 0), 3) != round(float(record.quantity or 0), 3)
              or money(linked.amount_due) != amount):
            milk_record, mismatches = "Differs from Finance", mismatches + 1
        else:
            milk_record = "Agrees"
        check = None
        if record.quantity is not None and record.unit_rate is not None:
            check = money(Decimal(str(record.quantity)) * Decimal(str(record.unit_rate))) - amount
        rows.append({
            "transaction_date": to_date(record.transaction_date),
            "sale_id": sale_id,
            "buyer": clean_text(record.counterparty),
            "litres": record.quantity,
            "rate": float(record.unit_rate) if record.unit_rate is not None else None,
            "amount": amount,
            "received": amount - outstanding,
            "outstanding": outstanding,
            "status": upper(record.status) or "RECORDED",
            "milk_record": milk_record,
            "amount_check": check,
            "payment_method": clean_text(record.payment_method),
            "due_date": record.due_date,
            "settled_date": record.settled_date,
        })

    litres = round(sum(float(r["litres"] or 0) for r in rows), 3)
    amount_total = sum((r["amount"] for r in rows), ZERO)
    notes = [
        "Milk Sales are Finance revenue transactions. Litres sold are not assumed to equal litres produced; "
        "see Milk Utilisation for the full disposition of produced milk.",
    ]
    if mismatches:
        notes.append(f"{mismatches} sale(s) do not agree with their Milk Sold record. Review the Milk Sold Record column.")
    if receipts_on_finance_sales:
        notes.append(
            f"{receipts_on_finance_sales} receipt posting(s) reference a Finance-originated sale. The primary sale "
            "is already revenue, so these postings should be reviewed for duplication."
        )
    return ReportResult(
        sections=[Section("sales", "Milk Sales", MILK_SALE_COLUMNS, rows, {
            "_label": "Total Milk Sales", "litres": litres, "amount": amount_total,
            "received": sum((r["received"] for r in rows), ZERO),
            "outstanding": sum((r["outstanding"] for r in rows), ZERO)}, primary=True)],
        summary=[
            Metric("litres", "Litres Sold", litres, "litres"),
            Metric("amount", "Sales Value", amount_total, "money"),
            Metric("avg_rate", "Average Rate / Litre", ratio(amount_total, litres, 4), "rate",
                   "Sales value divided by litres sold"),
            Metric("outstanding", "Outstanding", sum((r["outstanding"] for r in rows), ZERO), "money"),
        ],
        notes=notes,
    )


ANIMAL_SALE_COLUMNS = column_set(
    Column("transaction_date", "Date", "date"),
    Column("transaction_no", "Transaction No."),
    Column("sale_type", "Sale Type"),
    Column("animal_id", "Animal ID"),
    Column("animal_status", "Animal Status Now", "status"),
    Column("buyer", "Buyer"),
    Column("amount", "Amount (PKR)", "money", total=True),
    Column("received", "Received (PKR)", "money", total=True),
    Column("outstanding", "Outstanding (PKR)", "money", total=True),
    Column("status", "Status", "status"),
    Column("reference", "Reference", "text", "Details", "optional"),
)


def build_animal_sales(ctx: ReportContext) -> ReportResult:
    animals = ctx.animal_index()
    rows = []
    for record in ledger_rows(ctx, ctx.period.start, ctx.period.end):
        if not classifier.is_income(record) or upper(record.category) not in semantics.ANIMAL_SALE_CATEGORIES:
            continue
        amount = money(record.amount)
        outstanding = amount if semantics.is_outstanding(record) else ZERO
        animal = animals.get(str(record.animal_id)) if record.animal_id else None
        rows.append({
            "transaction_date": to_date(record.transaction_date),
            "transaction_no": f"FIN-{record.id}",
            "sale_type": semantics.category_label(record),
            "animal_id": clean_text(record.animal_id),
            "animal_status": upper(getattr(animal, "lifecycle_status", None)) or None,
            "buyer": clean_text(record.counterparty),
            "amount": amount, "received": amount - outstanding, "outstanding": outstanding,
            "status": upper(record.status) or "RECORDED",
            "reference": clean_text(record.reference),
        })
    unlinked = sum(1 for r in rows if not r["animal_id"])
    notes = []
    if unlinked:
        notes.append(f"{unlinked} animal sale(s) are not linked to an Animal ID.")
    not_exited = sum(1 for r in rows if r["animal_id"] and r["animal_status"] not in {"SOLD", None})
    if not_exited:
        notes.append(f"{not_exited} sold animal(s) are not marked SOLD in the herd register.")
    return ReportResult(
        sections=[Section("sales", "Animal Sales", ANIMAL_SALE_COLUMNS, rows, {
            "_label": "Total Animal Sales", "amount": sum((r["amount"] for r in rows), ZERO),
            "received": sum((r["received"] for r in rows), ZERO),
            "outstanding": sum((r["outstanding"] for r in rows), ZERO)}, primary=True)],
        summary=[Metric("count", "Animals Sold", len(rows), "integer"),
                 Metric("amount", "Sales Value", sum((r["amount"] for r in rows), ZERO), "money")],
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Cash-only movements
# ---------------------------------------------------------------------------

def build_cash_movements(ctx: ReportContext) -> ReportResult:
    rows = [
        transaction_row(r) for r in ledger_rows(ctx, ctx.period.start, ctx.period.end)
        if classifier.is_cash_inflow_only(r) or classifier.is_cash_movement_only(r)
    ]
    inflow = sum((r["active_amount"] for r in rows if r["nature"] == "Capital Inflow"), ZERO)
    outflow = sum((r["active_amount"] for r in rows if r["nature"] == "Cash Movement"), ZERO)
    return ReportResult(
        sections=[Section("cash", "Capital and Cash Movements", LEDGER_COLUMNS, rows, _ledger_totals(rows, "Total"), primary=True)],
        summary=[Metric("inflow", "Capital Inflows", inflow, "money"),
                 Metric("outflow", "Owner Draws and Loan Payments", outflow, "money")],
        notes=["These movements change the cash position but are neither farm revenue nor farm expenses, "
               "and never enter Cost of Milk."],
    )


# ---------------------------------------------------------------------------
# OPEX reconciliation: Finance -> OPEX -> OPEX/L -> COP
# ---------------------------------------------------------------------------

OPEX_GROUP_COLUMNS = column_set(
    Column("group", "Finance Expense Category"),
    Column("recorded", "Recorded in Period (PKR)", "money", total=True),
    Column("feed", "Feed, TMR Authority (PKR)", "money", total=True),
    Column("opex_eligible", "OPEX Eligible (PKR)", "money", total=True),
    Column("opex_excluded", "Non-OPEX Excluded (PKR)", "money", total=True),
    Column("used_in_coml", "Used in COML for Period (PKR)", "money", total=True),
)

OPEX_DETAIL_COLUMNS = column_set(
    Column("transaction_date", "Transaction Date", "date"),
    Column("transaction_no", "Transaction No."),
    Column("group", "Expense Category"),
    Column("item", "Expense Item"),
    Column("counterparty", "Counterparty", "text", "Details", "optional"),
    Column("amount", "Amount (PKR)", "money", total=True),
    Column("method", "Attribution Method"),
    Column("basis_dates", "Service / Coverage Dates"),
    Column("attributed", "Attributed to Period (PKR)", "money", total=True),
    Column("treatment", "Treatment"),
)

COP_TRACE_COLUMNS = column_set(
    Column("line", "Line"),
    Column("value", "Value", "number"),
    Column("unit", "Unit"),
    Column("source", "Authority"),
)

_TREATMENT = {
    "ATTRIBUTED": "Used in COML",
    "OUTSIDE_PERIOD": "OPEX, attributed to another period",
    "UNATTRIBUTED": "OPEX classification or attribution incomplete",
    "NON_OPEX": "Excluded: Non-OPEX",
}


def build_opex_reconciliation(ctx: ReportContext) -> ReportResult:
    from dairyos.api.coml import get_integrated_coml

    start, end = ctx.period.start, ctx.period.end
    effective_end = min(end, ctx.today)
    in_period = {r.id: r for r in ledger_rows(ctx, start, end) if classifier.is_expense(r)}

    attribution = (
        attribute_opex_for_period(ctx.factory, start, effective_end) if start <= ctx.today else None
    )
    attributed_rows = attribution.rows if attribution else []

    groups: dict[str, dict[str, Any]] = {}

    def bucket(name: str) -> dict[str, Any]:
        return groups.setdefault(name, {"group": name, "recorded": ZERO, "feed": ZERO, "opex_eligible": ZERO,
                                        "opex_excluded": ZERO, "used_in_coml": ZERO})

    for record in in_period.values():
        master, _code, group, _item = semantics.expense_category(record)
        amount = money(record.amount)
        line = bucket(group)
        line["recorded"] += amount
        if master == "Feed" or (master == "Legacy" and upper(record.category) == "FEED"):
            line["feed"] += amount
        elif is_operating_expense(record):
            line["opex_eligible"] += amount
        else:
            line["opex_excluded"] += amount

    detail = []
    for item in attributed_rows:
        record = item.transaction
        if item.status == "OUTSIDE_PERIOD" and record.id not in in_period:
            continue
        if item.status in {"NON_OPEX", "UNATTRIBUTED"} and record.id not in in_period:
            continue
        _master, _code, group, label = semantics.expense_category(record)
        if item.status == "ATTRIBUTED":
            bucket(group)["used_in_coml"] += item.attributed
        method = upper(record.cop_attribution_method) or None
        if method == "DIRECT":
            basis_dates = format_date(record.cop_service_date) if record.cop_service_date else None
        elif record.cop_coverage_start and record.cop_coverage_end:
            basis_dates = f"{format_date(record.cop_coverage_start)} to {format_date(record.cop_coverage_end)}"
        elif method == "CONSUMPTION":
            basis_dates = "Straws used in period"
        else:
            basis_dates = None
        detail.append({
            "transaction_date": to_date(record.transaction_date),
            "transaction_no": f"FIN-{record.id}",
            "group": group, "item": label,
            "counterparty": clean_text(record.counterparty),
            "amount": item.amount,
            "method": method.title() if method else None,
            "basis_dates": basis_dates,
            "attributed": item.attributed if item.status == "ATTRIBUTED" else ZERO,
            "treatment": _TREATMENT.get(item.status, item.status),
        })
    detail.sort(key=lambda r: (r["transaction_date"] or date.min, r["transaction_no"]))

    group_rows = sorted(groups.values(), key=lambda r: (-r["used_in_coml"], -r["recorded"], r["group"]))
    totals = {"_label": "Total"}
    for key in ("recorded", "feed", "opex_eligible", "opex_excluded", "used_in_coml"):
        totals[key] = sum((r[key] for r in group_rows), ZERO)

    cop = get_integrated_coml(period_start=start, period_end=end, container=ctx.container)
    costs = cop.get("costs", {})
    litres = cop.get("production", {}).get("totalLiters")
    cop_opex = money(costs.get("opex_total"))
    trace = [
        {"line": "OPEX attributed to period", "value": float(cop_opex), "unit": "PKR", "source": "Finance OPEX attribution"},
        {"line": "Milk produced", "value": litres, "unit": "litres", "source": "Milk production ledger"},
        {"line": "OPEX per litre", "value": costs.get("opex_cost_per_liter"), "unit": "PKR / litre", "source": "Estimated COP authority"},
        {"line": "Feed cost for period", "value": costs.get("feed_total"), "unit": "PKR", "source": "TMR feed cost authority"},
        {"line": "Feed cost per litre", "value": costs.get("feed_cost_per_liter"), "unit": "PKR / litre", "source": "Estimated COP authority"},
        {"line": "Cost of production per litre", "value": costs.get("total_coml_per_liter"), "unit": "PKR / litre",
         "source": "Estimated COP authority", "_emphasis": "total"},
    ]

    notes = [
        "Recorded amounts follow the transaction date. COML attribution follows the service date or coverage "
        "period of each expense, so an expense can be recorded in one period and used in COML in another.",
        "Feed purchases are recorded expenses but never enter OPEX: feed cost in COML comes from the TMR authority.",
    ]
    if end > ctx.today:
        notes.append(f"The period extends beyond the farm operational date. COML figures stop at {format_date(ctx.today)}.")
    unattributed = [r for r in detail if r["treatment"] == _TREATMENT["UNATTRIBUTED"]]
    if unattributed:
        notes.append(f"{len(unattributed)} OPEX transaction(s) lack a complete attribution and contribute PKR 0.00 to COML.")

    return ReportResult(
        sections=[
            Section("groups", "Finance to COML by Expense Category", OPEX_GROUP_COLUMNS, group_rows, totals),
            Section("detail", "Supporting Transactions", OPEX_DETAIL_COLUMNS, detail, {
                "_label": "Total", "amount": sum((r["amount"] for r in detail), ZERO),
                "attributed": sum((r["attributed"] for r in detail), ZERO)}, primary=True),
            Section("trace", "OPEX to Cost of Production", COP_TRACE_COLUMNS, trace),
        ],
        summary=[
            Metric("recorded", "Expenses Recorded", totals["recorded"], "money"),
            Metric("opex_eligible", "OPEX Eligible", totals["opex_eligible"], "money"),
            Metric("opex_excluded", "Non-OPEX Excluded", totals["opex_excluded"], "money"),
            Metric("used", "OPEX Used in COML", totals["used_in_coml"], "money"),
            Metric("opex_per_l", "OPEX / Litre", costs.get("opex_cost_per_liter"), "rate"),
        ],
        notes=notes,
        reconciliation=[
            ReconciliationCheck("Supporting transactions equal OPEX used by the COP authority", cop_opex,
                                totals["used_in_coml"]),
            ReconciliationCheck("Recorded equals Feed plus OPEX Eligible plus Non-OPEX", totals["recorded"],
                                totals["feed"] + totals["opex_eligible"] + totals["opex_excluded"]),
        ],
    )


# ---------------------------------------------------------------------------
# Semen purchases (Finance <-> Semen inventory)
# ---------------------------------------------------------------------------

SEMEN_PURCHASE_COLUMNS = column_set(
    Column("transaction_date", "Purchase Date", "date"),
    Column("transaction_no", "Transaction No."),
    Column("supplier", "Supplier"),
    Column("lot_code", "Semen Lot"),
    Column("sire", "Sire"),
    Column("semen_type", "Semen Type"),
    Column("straws", "Straws", "integer", total=True),
    Column("unit_cost", "Cost / Straw (PKR)", "rate"),
    Column("amount", "Amount (PKR)", "money", total=True),
    Column("lot_value", "Lot Value (PKR)", "money", total=True),
    Column("agreement", "Finance vs Lot"),
    Column("status", "Status", "status"),
)


def build_semen_purchases(ctx: ReportContext) -> ReportResult:
    records = [
        r for r in ledger_rows(ctx, ctx.period.start, ctx.period.end)
        if classifier.is_expense(r) and clean_text(r.sub_category) == "Semen Straws (Sexed / Conventional)"
    ]
    lots = {}
    if records:
        for lot in ctx.session.query(SemenLot).filter(
            SemenLot.purchase_transaction_id.in_([r.id for r in records])
        ).all():
            lots[lot.purchase_transaction_id] = lot
    rows = []
    for record in records:
        lot = lots.get(record.id)
        amount = money(record.amount)
        lot_value = money(Decimal(str(lot.unit_cost)) * Decimal(int(lot.purchased_quantity))) if lot else None
        rows.append({
            "transaction_date": to_date(record.transaction_date),
            "transaction_no": f"FIN-{record.id}",
            "supplier": clean_text(record.counterparty),
            "lot_code": getattr(lot, "lot_code", None),
            "sire": clean_text(getattr(lot, "bull_name", None)) or getattr(lot, "sire_code", None),
            "semen_type": getattr(lot, "semen_type", None),
            "straws": getattr(lot, "purchased_quantity", None),
            "unit_cost": float(lot.unit_cost) if lot else None,
            "amount": amount,
            "lot_value": lot_value,
            "agreement": "No semen lot linked" if lot is None else "Agrees" if lot_value == amount else "Differs",
            "status": upper(record.status) or "RECORDED",
        })
    return ReportResult(
        sections=[Section("purchases", "Semen Purchases", SEMEN_PURCHASE_COLUMNS, rows, {
            "_label": "Total", "straws": sum(int(r["straws"] or 0) for r in rows),
            "amount": sum((r["amount"] for r in rows), ZERO),
            "lot_value": sum(((r["lot_value"] or ZERO) for r in rows), ZERO)}, primary=True)],
        summary=[Metric("amount", "Semen Purchased", sum((r["amount"] for r in rows), ZERO), "money"),
                 Metric("straws", "Straws Purchased", sum(int(r["straws"] or 0) for r in rows), "integer")],
    )


# ---------------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------------

PARTY_FILTER = Filter("counterparty", "Counterparty contains", "text")


def _definition(report_id: str, title: str, purpose: str, builder, **kwargs) -> ReportDefinition:
    kwargs.setdefault("period", "range")
    kwargs.setdefault("authority", AUTHORITY)
    return ReportDefinition(id=report_id, area=AREA, title=title, purpose=purpose,
                            permission=PERMISSION, builder=builder, **kwargs)


REPORTS: tuple[ReportDefinition, ...] = (
    _definition(
        "fin-revenue-expense-reconciliation", "Revenue & Expense Reconciliation",
        "Revenue by category, expenses by category and the resulting management position for a month, "
        "a quarter or any date range, with control totals.",
        build_reconciliation, preset={"scope": "BOTH"}, default_period="MONTH", basis="RECORDED",
    ),
    _definition(
        "fin-revenue-reconciliation", "Revenue Reconciliation",
        "What revenue was recorded, what generated it, how much has been received and what is outstanding.",
        build_reconciliation, preset={"scope": "REVENUE"}, columns=REVENUE_COLUMNS, default_period="MONTH",
    ),
    _definition(
        "fin-expense-reconciliation", "Expense Reconciliation",
        "What expenses were recorded by governed category and item, what has been paid and what remains payable.",
        build_reconciliation, preset={"scope": "EXPENSE"}, columns=EXPENSE_COLUMNS, default_period="MONTH",
    ),
    _definition(
        "fin-periodic-summary", "Monthly / Quarterly Financial Summary",
        "Revenue, expenses and management position for each month or quarter of the selected range.",
        build_periodic_summary, columns=PERIODIC_COLUMNS, default_period="YEAR_TO_DATE",
        filters=(Filter("granularity", "Summarise by", options=(("MONTH", "Month"), ("QUARTER", "Quarter")),
                        default="MONTH"),),
    ),
    _definition(
        "fin-daily-activity", "Daily Financial Activity",
        "Revenue, expenses and cash-only movements for each day of the period.",
        build_daily_activity, columns=DAILY_COLUMNS, default_sort=("date", "asc"),
    ),
    _definition(
        "fin-transaction-ledger", "Transaction Ledger",
        "Every Finance transaction of the period with its full audit trail. The supporting detail behind every "
        "financial summary.",
        build_ledger, columns=LEDGER_COLUMNS, default_sort=("transaction_date", "asc"),
        filters=(
            NATURE_FILTER, STATUS_FILTER,
            Filter("category_group", "Category Group", "text"),
            Filter("category", "Category / Item", "text"),
            PARTY_FILTER,
            Filter("include_void", "Include VOID transactions", "toggle", default=True),
        ),
    ),
    _definition(
        "fin-receivables", "Receivables",
        "Revenue not yet received, by buyer and age, as of a date.",
        build_open_position, preset={"side": "RECEIVABLE"}, period="as_of",
        columns=POSITION_DETAIL_COLUMNS, filters=(PARTY_FILTER,), default_sort=("days_outstanding", "desc"),
        basis="DERIVED",
    ),
    _definition(
        "fin-payables", "Payables",
        "Expenses not yet paid, by supplier and age, as of a date.",
        build_open_position, preset={"side": "PAYABLE"}, period="as_of",
        columns=POSITION_DETAIL_COLUMNS, filters=(PARTY_FILTER,), default_sort=("days_outstanding", "desc"),
        basis="DERIVED",
    ),
    _definition(
        "fin-settlements", "Settlements",
        "Receivables received and payables paid during the period, by settled date.",
        build_settlements, columns=SETTLEMENT_COLUMNS, default_sort=("settled_date", "asc"),
        filters=(Filter("direction", "Direction", options=(("RECEIVED", "Received"), ("PAID", "Paid"))),),
    ),
    _definition(
        "fin-milk-sales", "Milk Sales",
        "Each milk sale with litres, rate, amount, settlement and agreement with the Milk Sold record.",
        build_milk_sales, columns=MILK_SALE_COLUMNS, default_sort=("transaction_date", "asc"),
        filters=(PARTY_FILTER,),
        authority="Finance MILK_SALES revenue linked to MilkDisposition (sale identity FIN-{transaction})",
    ),
    _definition(
        "fin-animal-sales", "Animal Sales",
        "Animals sold in the period with buyer, value, settlement and herd-register status.",
        build_animal_sales, columns=ANIMAL_SALE_COLUMNS, default_sort=("transaction_date", "asc"),
        authority="Finance animal-sale revenue linked to the Animal register",
    ),
    _definition(
        "fin-semen-purchases", "Semen Purchases",
        "Semen straw purchases reconciled to the semen lots they created.",
        build_semen_purchases, columns=SEMEN_PURCHASE_COLUMNS, default_sort=("transaction_date", "asc"),
        authority="Finance semen purchases linked to SemenLot.purchase_transaction_id",
    ),
    _definition(
        "fin-opex-reconciliation", "OPEX & Cost of Milk Reconciliation",
        "Traces Finance expenses to OPEX, to OPEX per litre and to cost of production, showing what is "
        "eligible, what is excluded and why.",
        build_opex_reconciliation, columns=OPEX_DETAIL_COLUMNS, default_period="MONTH", basis="CALCULATED",
        authority="Finance OPEX attribution policy and the Estimated COP authority (/farm/coml/integrated)",
    ),
    _definition(
        "fin-cash-movements", "Capital & Cash Movements",
        "Owner investment, owner draws and loan payments. Cash events that are neither revenue nor expense.",
        build_cash_movements, columns=LEDGER_COLUMNS, default_sort=("transaction_date", "asc"),
    ),
    _definition(
        "fin-void-history", "VOID Transaction History",
        "Every voided transaction with its original amount, prior status, reason and time of voiding.",
        build_void_history, columns=VOID_COLUMNS, default_sort=("transaction_date", "asc"),
    ),
)
