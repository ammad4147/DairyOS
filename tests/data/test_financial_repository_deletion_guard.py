from dataclasses import dataclass

import pytest

from dairyos.data.repositories.financial_repository import FinancialRepository


@dataclass
class FakeTransaction:
    id: int
    status: str = "RECORDED"
    notes: str | None = None


def test_financial_repository_delete_is_hard_blocked():
    repository = FinancialRepository()
    with pytest.raises(RuntimeError, match="Destructive deletion of financial transactions is prohibited"):
        repository.delete(1)


def test_financial_repository_void_requires_reason():
    transaction = FakeTransaction(id=1)
    repository = FinancialRepository()
    repository.records.append(transaction)

    with pytest.raises(ValueError, match="reason is required"):
        repository.void(1)


def test_financial_repository_void_preserves_record_as_void():
    transaction = FakeTransaction(id=1)
    repository = FinancialRepository()
    repository.records.append(transaction)

    result = repository.void(1, "Correction")

    assert result is transaction
    assert result.status == "VOID"
    assert "REASON=Correction" in result.notes


def test_financial_repository_void_cannot_bypass_settled_immutability():
    for status in ("PAID", "RECEIVED"):
        transaction = FakeTransaction(id=1, status=status)
        repository = FinancialRepository()
        repository.records.append(transaction)

        with pytest.raises(RuntimeError, match="settled financial transactions"):
            repository.void(1, "Correction")
