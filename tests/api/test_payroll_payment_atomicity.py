from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from dairyos.api.payroll import pay_payroll
from dairyos.data.database.session import engine
from dairyos.data.models.financial_transaction import FinancialTransaction
from dairyos.data.models.payroll import PayrollRecord
from dairyos.data.repositories.repository_factory import RepositoryFactory


def new_payroll():
    with Session(engine) as session, session.begin():
        record = PayrollRecord(
            employee_name="Atomicity test", employee_role="Milker",
            period_start=date(2026, 9, 1), period_end=date(2026, 9, 30),
            base_pay=Decimal("20000.01"), worked_days=Decimal("26"),
        )
        session.add(record)
        session.flush()
        return record.id


def test_failure_after_finance_flush_rolls_back_both_records(monkeypatch):
    record_id = new_payroll()

    def fail(*args):
        raise RuntimeError("injected failure after Finance flush")

    monkeypatch.setattr(PayrollRecord, "mark_paid", fail)
    with Session(engine) as runtime_session:
        container = SimpleNamespace(repository_factory=RepositoryFactory(runtime_session))
        with pytest.raises(RuntimeError, match="injected failure"):
            pay_payroll(record_id, container=container)
    with Session(engine) as session:
        record = session.get(PayrollRecord, record_id)
        assert record.status == "DRAFT"
        assert record.finance_transaction_id is None
        assert session.query(FinancialTransaction).filter_by(payroll_record_id=record_id).count() == 0


def test_concurrent_payments_share_one_posting_and_release_locks():
    record_id = new_payroll()
    barrier = Barrier(2)
    with Session(engine) as runtime_session:
        container = SimpleNamespace(repository_factory=RepositoryFactory(runtime_session))

        def pay():
            barrier.wait(timeout=10)
            return pay_payroll(record_id, container=container)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(pay) for _ in range(2)]
            results = [future.result(timeout=15) for future in futures]
        assert results[0]["finance_transaction_id"] == results[1]["finance_transaction_id"]
        assert not runtime_session.in_transaction()
    with Session(engine) as session:
        postings = session.query(FinancialTransaction).filter_by(payroll_record_id=record_id).all()
        assert len(postings) == 1
        assert postings[0].amount == Decimal("20000.01")
        assert session.get(PayrollRecord, record_id).status == "PAID"
