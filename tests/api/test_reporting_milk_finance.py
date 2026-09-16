from datetime import date, datetime
from types import SimpleNamespace

from dairyos.api import reporting


def test_plain_date_reduces_datetime_before_period_comparison():
    assert reporting._plain_date(datetime(2026, 9, 15, 6, 30)) == date(2026, 9, 15)


def test_milk_explicit_zero_is_not_changed_to_missing():
    row = SimpleNamespace(
        animal_id="T-001",
        production_date=datetime(2026, 9, 15, 6, 0),
        morning_yield=0.0,
        afternoon_yield=None,
        evening_yield=None,
        total_yield=0.0,
        status="RECORDED",
    )
    data = reporting._row(row)
    assert data["morning_yield"] == 0.0
    assert data["afternoon_yield"] is None


def test_finance_void_remains_audit_row_but_classifier_controls_totals():
    row = SimpleNamespace(type="INCOME", amount=100.0, status="VOID")
    assert reporting.finance_is_active(row) is False
    assert reporting.finance_is_income(row) is False


def test_owner_cash_movements_are_not_operating_income_or_expense():
    investment = SimpleNamespace(type="OWNER_INVESTMENT", amount=100.0, status="RECORDED")
    withdrawal = SimpleNamespace(type="OWNER_WITHDRAWAL", amount=50.0, status="RECORDED")
    assert reporting.finance_is_income(investment) is False
    assert reporting.finance_is_expense(investment) is False
    assert reporting.finance_is_income(withdrawal) is False
    assert reporting.finance_is_expense(withdrawal) is False


def test_reporting_non_opex_is_excluded_from_operating_expenses():
    records = [
        SimpleNamespace(
            type="INCOME",
            transaction_type="INCOME",
            amount=100000.0,
            status="RECORDED",
            master_category=None,
            cop_classification=None,
            date=date(2026, 9, 16),
        ),
        SimpleNamespace(
            type="EXPENSE",
            transaction_type="EXPENSE",
            amount=10000.0,
            status="RECORDED",
            master_category="OPEX",
            cop_classification="OPEX",
            date=date(2026, 9, 16),
        ),
        SimpleNamespace(
            type="EXPENSE",
            transaction_type="EXPENSE",
            amount=500000.0,
            status="RECORDED",
            master_category="NON_OPEX",
            sub_category="Equipment Purchase",
            cop_classification="NON_OPEX",
            date=date(2026, 9, 16),
        ),
        SimpleNamespace(
            type="EXPENSE",
            transaction_type="EXPENSE",
            amount=250000.0,
            status="RECORDED",
            master_category="OPEX",
            sub_category="Animal Purchase",
            cop_classification="NON_OPEX",
            date=date(2026, 9, 16),
        ),
    ]

    container = SimpleNamespace(
        finance=SimpleNamespace(
            get_all=lambda: records,
        )
    )

    payload = reporting.ReportingRequest(
        report_id="financial-summary",
        domain="FINANCE",
        period_mode="DATE_RANGE",
        start_date=date(2026, 9, 16),
        end_date=date(2026, 9, 16),
    )

    result = reporting._finance_dataset(
        payload,
        container,
        date(2026, 9, 16),
    )

    assert result["summary"]["operating_income"] == 100000.0
    assert result["summary"]["operating_expenses"] == 10000.0
    assert result["summary"]["non_operating_expenses"] == 750000.0
    assert result["summary"]["operating_net"] == 90000.0
    assert result["summary"]["audit_records"] == 4

    metrics = {
        row["metric"]: row["amount"]
        for row in result["rows"]
    }

    assert metrics["operating_income"] == 100000.0
    assert metrics["operating_expenses"] == 10000.0
    assert metrics["operating_net"] == 90000.0
