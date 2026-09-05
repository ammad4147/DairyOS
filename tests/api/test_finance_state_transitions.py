import pytest

from fastapi import HTTPException

from dairyos.api.finance_ledger import _validate_transition


@pytest.mark.parametrize(
    ("current", "requested"),
    [
        ("RECORDED", "PAYABLE"),
        ("RECORDED", "RECEIVABLE"),
        ("PAYABLE", "PAID"),
        ("RECEIVABLE", "RECEIVED"),
        ("RECORDED", "VOID"),
        ("PAYABLE", "VOID"),
        ("RECEIVABLE", "VOID"),
        ("PAID", "VOID"),
        ("RECEIVED", "VOID"),
    ],
)
def test_allowed_finance_transitions(current, requested):
    assert _validate_transition(current, requested) == requested


@pytest.mark.parametrize(
    ("current", "requested"),
    [
        ("PAID", "PAYABLE"),
        ("PAID", "RECORDED"),
        ("RECEIVED", "RECEIVABLE"),
        ("RECEIVED", "RECORDED"),
        ("VOID", "RECORDED"),
        ("VOID", "PAID"),
    ],
)
def test_forbidden_finance_transitions(current, requested):
    with pytest.raises(HTTPException) as exc:
        _validate_transition(current, requested)
    assert exc.value.status_code == 409


def test_unknown_status_is_rejected():
    with pytest.raises(HTTPException) as exc:
        _validate_transition("RECORDED", "UNKNOWN")
    assert exc.value.status_code == 422

def test_full_finance_lifecycle_preserves_transition_chronology(client):
    from datetime import date, timedelta
    from decimal import Decimal

    from dairyos.app import container
    from dairyos.data.models.financial_transaction import FinancialTransaction

    row = FinancialTransaction(
        transaction_type="EXPENSE",
        category="OTHER_OPERATING",
        amount=Decimal("1000.00"),
        status="RECORDED",
        due_date=date.today() + timedelta(days=7),
        notes="Audit lifecycle seed",
    )
    container.repository_factory.session.add(row)
    container.repository_factory.session.commit()
    container.repository_factory.session.refresh(row)
    transaction_id = row.id

    payable = client.post(
        f"/farm/finance-ledger/{transaction_id}/status",
        json={"status": "PAYABLE"},
    )
    assert payable.status_code == 200, payable.text

    paid = client.post(
        f"/farm/finance-ledger/{transaction_id}/status",
        json={"status": "PAID"},
    )
    assert paid.status_code == 200, paid.text
    settled_date = paid.json()["settled_date"]
    assert settled_date is not None

    voided = client.post(
        f"/farm/finance-ledger/{transaction_id}/status",
        json={"status": "VOID", "reason": "Audit correction"},
    )
    assert voided.status_code == 200, voided.text
    body = voided.json()

    assert body["status"] == "VOID"
    assert body["settled_date"] == settled_date
    assert body["notes"].count("STATUS_TRANSITION_AT=") == 3
    assert "FROM=RECORDED TO=PAYABLE" in body["notes"]
    assert "FROM=PAYABLE TO=PAID" in body["notes"]
    assert "FROM=PAID TO=VOID" in body["notes"]
    assert "REASON=Audit correction" in body["notes"]

