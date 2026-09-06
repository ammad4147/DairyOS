from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from dairyos.api.payroll import pay_payroll
from dairyos.data.models.payroll import PayrollRecord


class _PayrollRepo:
    def __init__(self, record):
        self.record = record

    def get_by_id(self, record_id):
        return self.record if self.record.id == record_id else None

    def get_all(self):
        return [self.record]

    def save(self, record):
        self.record = record
        return record

    def add(self, record):
        self.record = record
        return record


class _FinanceRepo:
    def __init__(self):
        self.rows = []

    def get_all(self):
        return list(self.rows)

    def add(self, row):
        row.id = len(self.rows) + 1
        self.rows.append(row)
        return row


class _Factory:
    def __init__(self, payroll_repo, finance_repo):
        self._payroll = payroll_repo
        self._finance = finance_repo

    def payroll(self):
        return self._payroll

    def finance(self):
        return self._finance


class _Container:
    def __init__(self, factory):
        self.repository_factory = factory


def _record():
    record = PayrollRecord(
        employee_name="Test Worker",
        employee_role="Milker",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        worked_days=Decimal("26"),
        base_pay=Decimal("26000"),
        overtime_hours=Decimal("4"),
        overtime_rate=Decimal("500"),
        allowances=Decimal("1000"),
        advances=Decimal("0"),
        deductions=Decimal("0"),
    )
    record.id = 1
    return record


def test_payroll_payment_posts_one_finance_transaction_and_is_idempotent():
    payroll = _PayrollRepo(_record())
    finance = _FinanceRepo()
    container = _Container(_Factory(payroll, finance))

    first = pay_payroll(1, payment_date=date(2026, 8, 31), container=container)
    second = pay_payroll(1, payment_date=date(2026, 8, 31), container=container)

    assert first["status"] == "PAID"
    assert first["finance_transaction_id"] == 1
    assert second["finance_transaction_id"] == 1
    assert len(finance.rows) == 1
    row = finance.rows[0]
    assert row.reference == "PAYROLL#1"
    assert row.payroll_record_id == 1
    assert row.master_category == "OPEX"
    assert row.category == "LABOUR"
    assert row.sub_category == "Milker Wages"
    assert row.cop_classification == "OPEX"
    assert row.cop_attribution_method == "PERIODIC"
    assert row.cop_coverage_start == date(2026, 8, 1)
    assert row.cop_coverage_end == date(2026, 8, 31)
