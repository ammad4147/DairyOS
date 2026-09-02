from datetime import date
from types import SimpleNamespace

from dairyos.farm.production.services.milk_inventory_capacity_service import (
    overall_saleable_capacity,
)


class _Repo:
    def __init__(self, rows):
        self.rows = rows

    def get_all(self):
        return list(self.rows)


class _Factory:
    def __init__(self, production, dispositions):
        self._production = _Repo(production)
        self._dispositions = _Repo(dispositions)

    def milk(self):
        return self._production

    def milk_dispositions(self):
        return self._dispositions


def _production(day, litres, status="RECORDED"):
    return SimpleNamespace(
        production_date=day,
        total_yield=litres,
        status=status,
    )


def _disposition(day, litres, kind="SOLD", row_id=None, status="RECORDED"):
    return SimpleNamespace(
        id=row_id,
        production_date=day,
        quantity_litres=litres,
        disposition_type=kind,
        status=status,
    )


def test_historical_orphan_sale_does_not_consume_future_saleable_milk():
    factory = _Factory(
        production=[
            _production(date(2026, 9, 1), 50.0),
            _production(date(2026, 9, 2), 30.0, "WITHDRAWAL"),
            _production(date(2026, 9, 2), 288.0),
        ],
        dispositions=[
            _disposition(date(2026, 8, 31), 60.0, "SOLD", 429),
            _disposition(date(2026, 9, 2), 5.0, "DOMESTIC_USE", 430),
            _disposition(date(2026, 9, 2), 5.0, "CALF_FEED", 431),
            _disposition(date(2026, 9, 2), 5.0, "WASTAGE", 432),
            _disposition(date(2026, 9, 2), 200.0, "SOLD", 433),
        ],
    )

    result = overall_saleable_capacity(
        date(2026, 9, 2),
        factory=factory,
    )

    assert result["biological_production_litres"] == 368.0
    assert result["withdrawal_litres"] == 30.0
    assert result["saleable_production_litres"] == 338.0
    assert result["ordinary_accounted_litres"] == 215.0
    assert result["unbacked_disposition_litres"] == 60.0
    assert result["available_saleable_litres"] == 123.0
