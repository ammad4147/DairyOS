from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from dairyos.api import farm_intelligence
from dairyos.core.time_utils import utcnow


class _Repo:
    def __init__(self, rows):
        self._rows = rows

    def get_all(self):
        return list(self._rows)


class _Factory:
    def __init__(self, finance_rows):
        self._empty = _Repo([])
        self._finance = _Repo(finance_rows)
        self.closed = False

    def animal(self):
        return self._empty

    def milk(self):
        return self._empty

    def feed(self):
        return self._empty

    def finance(self):
        return self._finance

    def breeding(self):
        return self._empty

    def health(self):
        return self._empty

    def treatment(self):
        return self._empty

    def close(self):
        self.closed = True


def _txn(transaction_type: str, status: str, amount: float):
    return SimpleNamespace(
        transaction_type=transaction_type,
        status=status,
        amount=amount,
        transaction_date=utcnow() - timedelta(days=1),
    )


def test_farm_kpis_use_canonical_active_finance_classification(monkeypatch):
    factory = _Factory(
        [
            _txn("EXPENSE", "PAID", 100),
            _txn("PAYMENT", "PAID", 20),
            _txn("EXPENSE", "VOID", 1000),
            _txn("RECEIPT", "RECEIVED", 500),
            _txn("INCOME", "CANCELLED", 5000),
        ]
    )
    monkeypatch.setattr(farm_intelligence, "_factory", lambda: factory)

    result = farm_intelligence.dairy_kpis(days=30)

    assert result["values"]["expenses"] == 120.0
    assert result["values"]["income"] == 500.0
    assert result["values"]["net_cash_movement"] == 380.0
    assert factory.closed is True
