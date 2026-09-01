from dataclasses import dataclass

import pytest

from dairyos.data.repositories.financial_repository import FinancialRepository


@dataclass
class FakeTransaction:
    id: int
    status: str = "RECORDED"
    notes: str | None = None
    transaction_type: str = "EXPENSE"
    amount: float = 0.0
    animal_id: str | None = None
    settled_date: str | None = None


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


def test_financial_repository_voids_settled_rows_without_erasing_settlement_history():
    for status in ("PAID", "RECEIVED"):
        transaction = FakeTransaction(
            id=1,
            status=status,
            settled_date="2026-09-01",
        )
        repository = FinancialRepository()
        repository.records.append(transaction)

        result = repository.void(1, "Correction")

        assert result is transaction
        assert result.status == "VOID"
        assert result.settled_date == "2026-09-01"
        assert "REASON=Correction" in result.notes


def test_financial_repository_totals_exclude_void_rows():
    repository = FinancialRepository()
    repository.records.extend(
        [
            FakeTransaction(id=1, transaction_type="INCOME", amount=100.0),
            FakeTransaction(
                id=2,
                status="VOID",
                transaction_type="RECEIPT",
                amount=900.0,
            ),
            FakeTransaction(id=3, transaction_type="EXPENSE", amount=40.0),
            FakeTransaction(
                id=4,
                status="VOID",
                transaction_type="PAYMENT",
                amount=600.0,
            ),
        ]
    )

    assert repository.total_income() == 100.0
    assert repository.total_expenses() == 40.0
    assert repository.net_balance() == 60.0


def test_financial_repository_animal_profitability_excludes_void_rows():
    repository = FinancialRepository()
    repository.records.extend(
        [
            FakeTransaction(
                id=1,
                animal_id="AN-001",
                transaction_type="RECEIPT",
                amount=250.0,
            ),
            FakeTransaction(
                id=2,
                animal_id="AN-001",
                status="VOID",
                transaction_type="INCOME",
                amount=750.0,
            ),
            FakeTransaction(
                id=3,
                animal_id="AN-001",
                transaction_type="PAYMENT",
                amount=80.0,
            ),
            FakeTransaction(
                id=4,
                animal_id="AN-001",
                status="VOID",
                transaction_type="EXPENSE",
                amount=420.0,
            ),
        ]
    )

    assert repository.get_animal_profitability("AN-001") == {
        "animal_id": "AN-001",
        "total_income": 250.0,
        "total_expenses": 80.0,
        "net_profit": 170.0,
    }
