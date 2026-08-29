from datetime import date
from decimal import Decimal

from dairyos.data.models.payroll import PayrollRecord
from dairyos.data.repositories.payroll_repository import PayrollRepository


def test_payroll_record_calculates_gross_and_net_pay():
    record = PayrollRecord(
        employee_name="Test Employee",
        employee_role="MILKER",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        worked_days=Decimal("26"),
        base_pay=Decimal("50000"),
        overtime_hours=Decimal("10"),
        overtime_rate=Decimal("500"),
        allowances=Decimal("5000"),
        advances=Decimal("2000"),
        deductions=Decimal("1000"),
    )

    assert record.overtime_pay == Decimal("5000")
    assert record.gross_pay == Decimal("60000")
    assert record.net_pay == Decimal("57000")


def test_payroll_repository_totals_are_period_neutral_and_decimal_safe():
    first = PayrollRecord(
        employee_name="A",
        employee_role="MILKER",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        base_pay=Decimal("40000"),
        allowances=Decimal("2000"),
    )
    second = PayrollRecord(
        employee_name="B",
        employee_role="FEEDER",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        base_pay=Decimal("30000"),
        deductions=Decimal("1000"),
    )

    totals = PayrollRepository.totals([first, second])

    assert totals["record_count"] == 2
    assert totals["gross_pay"] == Decimal("72000")
    assert totals["net_pay"] == Decimal("71000")
    assert totals["deductions"] == Decimal("1000")


def test_payroll_record_can_be_marked_paid():
    record = PayrollRecord(
        employee_name="A",
        employee_role="VETERINARIAN",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
    )

    record.mark_paid(date(2026, 9, 1))

    assert record.status == "PAID"
    assert record.payment_date == date(2026, 9, 1)
