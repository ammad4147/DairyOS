from types import SimpleNamespace

from dairyos.api.feed_inventory import _finance_purchase_rows
from dairyos.api.feed_management import _historical_feed_cost


class Repo:
    def __init__(self, rows):
        self.rows = rows

    def get_all(self):
        return list(self.rows)


class Factory:
    def __init__(self, rows):
        self._finance = Repo(rows)

    def finance(self):
        return self._finance


def row(*, status="RECORDED", transaction_type="EXPENSE", rate=50.0, quantity=10.0):
    return SimpleNamespace(
        id=1,
        status=status,
        transaction_type=transaction_type,
        master_category="FEED",
        sub_category="Silage",
        transaction_date=__import__("datetime").datetime(2026, 9, 1, 8, 0),
        unit="kg",
        unit_rate=rate,
        quantity=quantity,
        amount=rate * quantity,
    )


def test_feed_purchase_authority_excludes_all_inactive_finance_statuses():
    factory = Factory(
        [
            row(status="VOID"),
            row(status="CANCELLED"),
            row(status="DELETED"),
            row(status="RECORDED", transaction_type="PAYMENT"),
        ]
    )

    rows = _finance_purchase_rows(factory, "Silage")

    assert len(rows) == 1
    assert rows[0].transaction_type == "PAYMENT"


def test_historical_feed_cost_never_uses_inactive_finance_row():
    factory = Factory(
        [
            row(status="DELETED", rate=999.0),
            row(status="RECORDED", transaction_type="PAYMENT", rate=55.0),
        ]
    )

    result = _historical_feed_cost(
        factory,
        "Silage",
        __import__("datetime").datetime(2026, 9, 1, 12, 0),
    )

    assert result is not None
    assert result["unit_cost_per_kg"] == 55.0
