from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from dairyos.app import app
from dairyos.data.database.session import SessionLocal
from dairyos.data.models.financial_transaction import FinancialTransaction


@pytest.fixture
def finance_test_ids():
    ids: list[int] = []
    yield ids
    if not ids:
        return
    session = SessionLocal()
    try:
        session.query(FinancialTransaction).filter(FinancialTransaction.id.in_(ids)).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


client = TestClient(app)


def create_expense(test_ids: list[int], **overrides):
    payload = {
        "transaction_type": "EXPENSE",
        "master_category": "FEED",
        "sub_category": "Molasses",
        "quantity": 10,
        "unit": "kg",
        "unit_rate": 100,
        "transaction_date": date.today().isoformat(),
        "payment_method": "BANK",
        "counterparty": "Test Feed Supplier",
        "status": "PAID",
    }
    payload.update(overrides)
    response = client.post("/farm/finance-ledger", json=payload)
    if response.status_code < 300:
        test_ids.append(response.json()["id"])
    return response


def test_settled_expense_requires_governed_correction(finance_test_ids):
    created = create_expense(finance_test_ids)
    assert created.status_code == 200, created.text
    original = created.json()
    assert original["amount"] == 1000
    assert original["status"] == "PAID"

    edited = client.patch(
        f"/farm/finance-ledger/{original['id']}",
        json={"quantity": 15, "unit": "kg", "unit_rate": 120},
    )
    assert edited.status_code == 409, edited.text
    assert "Settled transactions" in edited.json()["detail"]


def test_void_transaction_cannot_be_edited(finance_test_ids):
    created = create_expense(
        finance_test_ids,
        status="PAYABLE",
        payment_method="CREDIT",
        due_date=(date.today() + timedelta(days=7)).isoformat(),
    )
    assert created.status_code == 200, created.text
    transaction_id = created.json()["id"]

    voided = client.post(
        f"/farm/finance-ledger/{transaction_id}/status",
        json={"status": "VOID", "reason": "Test correction"},
    )
    assert voided.status_code == 200, voided.text

    edited = client.patch(
        f"/farm/finance-ledger/{transaction_id}",
        json={"amount": 2500},
    )
    assert edited.status_code == 409


def test_payable_requires_due_date_and_reports_ageing(finance_test_ids):
    transaction_date = date.today() - timedelta(days=35)
    due_date = date.today() - timedelta(days=35)
    created = create_expense(
        finance_test_ids,
        transaction_date=transaction_date.isoformat(),
        payment_method="CREDIT",
        status="PAYABLE",
        due_date=due_date.isoformat(),
        counterparty="ABC Supplier",
    )
    assert created.status_code == 200, created.text

    payables = client.get("/farm/finance-ledger/ageing")
    assert payables.status_code == 200, payables.text
    body = payables.json()
    assert body["outstanding_total"] == 1000
    assert body["overdue_total"] == 1000
    assert body["ageing_buckets"]["31_60"] == 1000
    assert body["supplier_rollup"][0]["supplier"] == "ABC Supplier"
    assert body["transactions"][0]["days_overdue"] == 35


def test_payable_settlement_removes_it_from_outstanding_and_records_settled_date(finance_test_ids):
    created = create_expense(
        finance_test_ids,
        payment_method="CREDIT",
        status="PAYABLE",
        due_date=(date.today() + timedelta(days=7)).isoformat(),
    )
    assert created.status_code == 200, created.text
    transaction_id = created.json()["id"]

    paid = client.post(
        f"/farm/finance-ledger/{transaction_id}/status",
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text
    paid_body = paid.json()
    assert paid_body["status"] == "PAID"
    assert paid_body["settled_date"] == date.today().isoformat()

    payables = client.get("/farm/finance-ledger/ageing")
    assert payables.status_code == 200, payables.text
    assert payables.json()["outstanding_total"] == 0
    assert payables.json()["count"] == 0


def test_due_date_before_transaction_date_is_rejected(finance_test_ids):
    created = create_expense(
        finance_test_ids,
        transaction_date=date.today().isoformat(),
        payment_method="CREDIT",
        status="PAYABLE",
        due_date=(date.today() - timedelta(days=1)).isoformat(),
    )
    assert created.status_code == 422
