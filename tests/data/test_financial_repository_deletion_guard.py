import pytest

from dairyos.data.repositories.financial_repository import FinancialRepository


def test_financial_repository_delete_is_hard_blocked():
    repository = FinancialRepository()
    with pytest.raises(RuntimeError, match="Destructive deletion of financial transactions is prohibited"):
        repository.delete(1)
