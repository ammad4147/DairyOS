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
