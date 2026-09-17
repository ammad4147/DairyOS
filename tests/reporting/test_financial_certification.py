"""Deterministic financial certification of DairyOS Reporting.

Expected values are constants declared in ``synthetic_farm.EXPECTED`` and
derived by hand from the fixtures. An unexplained difference must be
PKR 0.00. The evidence table is written to ``.certification`` for the
final report.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from tests.reporting.conftest import metric, section
from tests.reporting.synthetic_farm import EXPECTED

D = Decimal
SEPTEMBER = {"mode": "MONTH", "year": 2026, "month": 9}
Q3 = {"mode": "QUARTER", "year": 2026, "quarter": 3}
CUSTOM = {"mode": "CUSTOM", "start_date": "2026-08-10", "end_date": "2026-09-17"}
EVIDENCE: list[dict] = []
EVIDENCE_PATH = Path(__file__).resolve().parents[2] / ".certification" / "financial_acceptance_evidence.json"


def money(value) -> Decimal:
    return D(str(value)).quantize(D("0.01"))


def certify(check: str, expected: Decimal, actual) -> None:
    actual = money(actual)
    EVIDENCE.append({"check": check, "expected": f"{expected:.2f}", "actual": f"{actual:.2f}",
                     "difference": f"{actual - expected:.2f}", "result": "PASS" if actual == expected else "FAIL"})
    assert actual == expected, f"{check}: expected PKR {expected:,.2f}, actual PKR {actual:,.2f}"


@pytest.fixture(scope="module", autouse=True)
def _write_evidence():
    yield
    EVIDENCE_PATH.parent.mkdir(exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(EVIDENCE, indent=2), encoding="utf-8")


def _controls_pass(body):
    assert body["reconciliation"], "financial reports publish their control totals"
    for control in body["reconciliation"]:
        assert control["status"] == "PASS", control
        assert money(control["difference"]) == D("0.00")


# ---------------------------------------------------------------- periods
def test_monthly_period_resolves_to_calendar_month(run):
    body = run("fin-revenue-expense-reconciliation", period=SEPTEMBER)
    assert (body["period"]["start_date"], body["period"]["end_date"]) == ("2026-09-01", "2026-09-30")
    assert "September 2026" in body["period"]["label"]


def test_quarter_three_resolves_to_july_through_september(run):
    body = run("fin-revenue-expense-reconciliation", period=Q3)
    assert (body["period"]["start_date"], body["period"]["end_date"]) == ("2026-07-01", "2026-09-30")
    assert body["period"]["label"].startswith("Q3 2026")


def test_monthly_reconciliation(run):
    body = run("fin-revenue-expense-reconciliation", period=SEPTEMBER)
    certify("Monthly Revenue", EXPECTED["sep_revenue_total"], metric(body, "total_revenue"))
    certify("Monthly Expenses", EXPECTED["sep_expenses_total"], metric(body, "total_expenses"))
    certify("Monthly Revenue less Expenses", EXPECTED["sep_position"], metric(body, "position"))
    _controls_pass(body)

    revenue = section(body, "revenue")
    by_group: dict[str, Decimal] = {}
    for row in revenue["rows"]:
        by_group[row["group"]] = by_group.get(row["group"], D("0")) + money(row["gross"])
    assert by_group == EXPECTED["sep_revenue"]
    assert money(revenue["totals"]["gross"]) == sum(by_group.values())
    assert money(revenue["totals"]["received"]) + money(revenue["totals"]["outstanding"]) == EXPECTED["sep_revenue_total"]
    milk = next(r for r in revenue["rows"] if r["category"] == "Milk Sales")
    assert (milk["transactions"], milk["quantity"], milk["unit"]) == (12, 4800.0, "litre")

    expenses = section(body, "expenses")
    by_class: dict[str, Decimal] = {}
    for row in expenses["rows"]:
        by_class[row["master"]] = by_class.get(row["master"], D("0")) + money(row["amount"])
    assert by_class == EXPECTED["sep_expense_classes"]
    assert round(sum(r["share"] for r in expenses["rows"]), 0) == 100

    labels = " ".join(str(r["line"]) for r in section(body, "position")["rows"]).lower()
    for forbidden in ("profit", "ebitda", "net income", "cash flow"):
        assert forbidden not in labels


def test_quarterly_reconciliation(run):
    body = run("fin-revenue-expense-reconciliation", period=Q3)
    certify("Quarterly Revenue", EXPECTED["q3_revenue"], metric(body, "total_revenue"))
    certify("Quarterly Expenses", EXPECTED["q3_expenses"], metric(body, "total_expenses"))
    _controls_pass(body)


def test_custom_range_reconciliation_and_boundaries(run):
    body = run("fin-revenue-expense-reconciliation", period=CUSTOM)
    certify("Custom Revenue", EXPECTED["custom_revenue"], metric(body, "total_revenue"))
    certify("Custom Expenses", EXPECTED["custom_expenses"], metric(body, "total_expenses"))
    _controls_pass(body)

    ledger = run("fin-transaction-ledger", period=CUSTOM, filters={"category": "Other Revenue"})
    amounts = sorted(money(r["amount"]) for r in section(ledger, "ledger")["rows"])
    # exactly From (2,222), within (3,333), exactly To (15,556) are in;
    # the day before From (1,111) and the day after To (4,444) are out.
    assert amounts == [D("2222.00"), D("3333.00"), D("15556.00")]


def test_same_day_range_and_from_after_to(run):
    body = run("fin-revenue-expense-reconciliation",
               period={"mode": "CUSTOM", "start_date": "2026-09-05", "end_date": "2026-09-05"})
    assert money(metric(body, "total_revenue")) == D("130000.00")  # milk 100,000 + manure 30,000
    error = run("fin-revenue-expense-reconciliation", expect=422,
                period={"mode": "CUSTOM", "start_date": "2026-09-10", "end_date": "2026-09-01"})
    assert "on or before" in error["detail"]


# ------------------------------------------------- summary -> category -> detail
def test_every_category_total_is_supported_by_transaction_detail(run):
    summary = run("fin-revenue-expense-reconciliation", period=SEPTEMBER)
    for section_id, key in (("revenue", "gross"), ("expenses", "amount")):
        for row in section(summary, section_id)["rows"]:
            drill = row["_drill"]
            detail = run(drill["report_id"], period=drill["period"], filters=drill["filters"])
            supported = sum((money(r["active_amount"]) for r in section(detail, "ledger")["rows"]), D("0"))
            assert supported == money(row[key]), (row, supported)
            assert money(section(detail, "ledger")["totals"]["active_amount"]) == money(row[key])


def test_periodic_summary_reconciles_to_quarter(run):
    months = run("fin-periodic-summary", period=Q3, filters={"granularity": "MONTH"})
    rows = section(months, "periods")["rows"]
    assert [r["period"] for r in rows] == ["July 2026", "August 2026", "September 2026"]
    assert money(rows[2]["revenue"]) == EXPECTED["sep_revenue_total"]
    assert money(section(months, "periods")["totals"]["revenue"]) == EXPECTED["q3_revenue"]
    quarter = run("fin-periodic-summary", period=Q3, filters={"granularity": "QUARTER"})
    assert money(section(quarter, "periods")["rows"][0]["expenses"]) == EXPECTED["q3_expenses"]
    _controls_pass(months)


def test_daily_activity_sums_to_month(run):
    body = run("fin-daily-activity", period=SEPTEMBER)
    totals = section(body, "days")["totals"]
    assert money(totals["revenue"]) == EXPECTED["sep_revenue_total"]
    assert money(totals["expenses"]) == EXPECTED["sep_expenses_total"]
    assert money(totals["capital_in"]) == D("500000.00") and money(totals["cash_out"]) == D("40000.00")


# ------------------------------------------------------------------ VOID
def test_void_is_visible_in_history_and_excluded_everywhere(run):
    count, amount = EXPECTED["sep_void"]
    history = run("fin-void-history", period=SEPTEMBER)
    rows = section(history, "void")["rows"]
    assert len(rows) == count and sum(money(r["amount"]) for r in rows) == amount
    assert {r["void_reason"] for r in rows} == {"Entered twice", "Wrong amount"}
    assert {r["status_before"] for r in rows} == {"RECEIVABLE", "RECORDED"}

    ledger = run("fin-transaction-ledger", period=SEPTEMBER, filters={"status": "VOID"})
    void_rows = section(ledger, "ledger")["rows"]
    assert len(void_rows) == count
    assert all(money(r["active_amount"]) == 0 and money(r["outstanding_amount"]) == 0 for r in void_rows)

    hidden = run("fin-transaction-ledger", period=SEPTEMBER, filters={"include_void": False})
    assert all(r["status"] != "VOID" for r in section(hidden, "ledger")["rows"])
    certify("VOID excluded from Monthly Revenue", EXPECTED["sep_revenue_total"],
            metric(run("fin-revenue-reconciliation", period=SEPTEMBER), "total_revenue"))


# --------------------------------------------- receivables, payables, settlements
def test_receivables(run):
    body = run("fin-receivables")
    certify("Receivables", EXPECTED["receivables"], metric(body, "outstanding"))
    certify("Receivables Overdue", EXPECTED["receivables_overdue"], metric(body, "overdue"))
    _controls_pass(body)
    rows = section(body, "detail")["rows"]
    assert len(rows) == 3 and all(money(r["settled_amount"]) == 0 for r in rows)
    overdue = next(r for r in rows if r["days_overdue"])
    assert (overdue["days_overdue"], overdue["age_bucket"], overdue["days_outstanding"]) == (4, "1 to 30 days overdue", 7)
    parties = {r["party"]: money(r["outstanding_amount"]) for r in section(body, "parties")["rows"]}
    assert parties == {"Lahore Milk Co": D("200000.00"), "Rana Livestock": D("150000.00")}


def test_receivables_as_of_a_historical_date(run):
    body = run("fin-receivables", period={"as_of_date": "2026-09-05"})
    certify("Receivables as of 05-Sep-2026", EXPECTED["receivables_as_of_sep5"], metric(body, "outstanding"))
    assert {r["current_status"] for r in section(body, "detail")["rows"]} == {"RECEIVED"}


def test_payables(run):
    body = run("fin-payables")
    certify("Payables", EXPECTED["payables"], metric(body, "outstanding"))
    certify("Payables Overdue", EXPECTED["payables_overdue"], metric(body, "overdue"))
    _controls_pass(body)


def test_settlements(run):
    body = run("fin-settlements", period=SEPTEMBER)
    certify("Settlements Received", EXPECTED["settled_received"], metric(body, "received"))
    certify("Settlements Paid", EXPECTED["settled_paid"], metric(body, "paid"))
    assert {r["days_to_settle"] for r in section(body, "settlements")["rows"] if r["direction"] == "Received"} == {2}


def test_settlement_lifecycle_through_the_finance_api(farm, run):
    """Original transaction -> settlement -> settled -> outstanding -> status."""
    sale_id = farm.handles["sales"]["2026-09-11"]
    before = money(metric(run("fin-receivables"), "outstanding"))
    response = farm.post(f"/farm/finance-ledger/{sale_id}/status", json={"status": "RECEIVED"})
    assert response.status_code == 200, response.text
    try:
        after = run("fin-receivables")
        assert money(metric(after, "outstanding")) == before - D("100000.00")
        assert f"FIN-{sale_id}" not in {r["transaction_no"] for r in section(after, "detail")["rows"]}
        settled = run("fin-settlements", period={"mode": "CUSTOM", "start_date": "2026-09-18", "end_date": "2026-09-18"})
        assert f"FIN-{sale_id}" in {r["transaction_no"] for r in section(settled, "settlements")["rows"]}
        sales = run("fin-milk-sales", period=SEPTEMBER)
        row = next(r for r in section(sales, "sales")["rows"] if r["sale_id"] == f"FIN-{sale_id}")
        assert (row["status"], money(row["outstanding"]), row["milk_record"]) == ("RECEIVED", D("0.00"), "Agrees")
    finally:
        from tests import conftest as root
        from dairyos.data.models.financial_transaction import FinancialTransaction
        from dairyos.data.models.milk_disposition import MilkDisposition
        db = root.container.repository_factory.session
        row = db.get(FinancialTransaction, sale_id)
        row.status, row.settled_date = "RECEIVABLE", None
        row.notes = None
        db.query(MilkDisposition).filter(MilkDisposition.sale_id == f"FIN-{sale_id}").update({"amount_received": 0})
        db.commit()


# ------------------------------------------------------------ cross-module
def test_milk_sales_reconcile_to_finance_and_milk(run):
    body = run("fin-milk-sales", period=SEPTEMBER)
    totals = section(body, "sales")["totals"]
    certify("Milk Sales equal Revenue category", EXPECTED["sep_revenue"]["Milk Sales"], totals["amount"])
    assert totals["litres"] == 4800.0 and metric(body, "avg_rate") == 250.0
    rows = section(body, "sales")["rows"]
    assert {r["milk_record"] for r in rows} == {"Agrees"}
    assert run("fin-milk-sales", period=SEPTEMBER, columns=["sale_id", "amount_check"])  # column customisation
    utilisation = run("milk-utilisation", period=SEPTEMBER)
    assert section(utilisation, "utilisation")["totals"]["sold"] == 4800.0
    assert money(section(utilisation, "utilisation")["totals"]["sale_value"]) == EXPECTED["sep_revenue"]["Milk Sales"]


def test_animal_sales_and_semen_purchases(run):
    animals = run("fin-animal-sales", period=SEPTEMBER)
    row = section(animals, "sales")["rows"][0]
    assert (row["animal_id"], row["animal_status"], money(row["amount"])) == ("XS001", "SOLD", D("150000.00"))
    semen = run("fin-semen-purchases", period=SEPTEMBER)
    row = section(semen, "purchases")["rows"][0]
    assert (row["lot_code"], row["straws"], row["agreement"]) == ("SL-001", 20, "Agrees")
    assert money(row["amount"]) == money(row["lot_value"]) == D("40000.00")


def test_opex_reconciles_to_the_cop_authority(farm, run):
    body = run("fin-opex-reconciliation", period=SEPTEMBER)
    certify("OPEX", EXPECTED["sep_opex"], metric(body, "used"))
    _controls_pass(body)
    totals = section(body, "groups")["totals"]
    assert money(totals["recorded"]) == EXPECTED["sep_expenses_total"]
    assert money(totals["feed"]) == D("500000.00")
    assert money(totals["opex_eligible"]) == D("190000.00")
    assert money(totals["opex_excluded"]) == D("60000.00")          # Equipment Purchase
    detail = {r["item"]: r for r in section(body, "detail")["rows"]}
    assert money(detail["Electricity / Power"]["attributed"]) == D("42000.00")
    assert money(detail["Antibiotics & General Medications"]["attributed"]) == D("18000.00")
    assert money(detail["Semen Straws (Sexed / Conventional)"]["attributed"]) == D("6000.00")
    assert detail["Equipment Purchase"]["treatment"] == "Excluded: Non-OPEX"
    assert "FIN-" in detail["Electricity / Power"]["transaction_no"]

    authority = farm.get("/farm/coml/integrated", params={"period_start": "2026-09-01", "period_end": "2026-09-30"}).json()
    certify("OPEX equals COML authority input", money(authority["costs"]["opex_total"]), metric(body, "used"))
    cost = run("cost-period", period=SEPTEMBER)
    certify("COML Feed Cost", EXPECTED["sep_feed_cost"], section(cost, "cost")["rows"][0]["feed_cost"])
    expected_cop = round(float(EXPECTED["sep_feed_cost"] + EXPECTED["sep_opex"]) / EXPECTED["milk_sep"], 4)
    assert metric(cost, "cop") == authority["costs"]["total_coml_per_liter"] == expected_cop
    _controls_pass(cost)


def test_cash_movements_are_neither_revenue_nor_expense(run):
    body = run("fin-cash-movements", period=SEPTEMBER)
    assert money(metric(body, "inflow")) == D("500000.00") and money(metric(body, "outflow")) == D("40000.00")


def test_no_financial_report_exposes_implementation_fields(run):
    body = run("fin-transaction-ledger", period=SEPTEMBER)
    keys = {c["key"] for c in section(body, "ledger")["columns"]}
    assert not keys & {"id", "cop_classification", "payroll_record_id", "feed_record_id", "milk_sale_id"}
    assert "STATUS_TRANSITION_AT" not in json.dumps([r.get("notes") for r in section(body, "ledger")["rows"]])
