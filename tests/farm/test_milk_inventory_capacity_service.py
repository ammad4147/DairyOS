from datetime import date, datetime
from types import SimpleNamespace

from dairyos.farm.production.services.milk_inventory_capacity_service import (
    overall_saleable_capacity,
)


class Repo:
    def __init__(self, rows):
        self.rows = rows

    def get_all(self):
        return list(self.rows)


class Factory:
    def __init__(self, production, dispositions):
        self._production = Repo(production)
        self._dispositions = Repo(dispositions)

    def milk(self):
        return self._production

    def milk_dispositions(self):
        return self._dispositions


def production(day, litres, status="RECORDED"):
    return SimpleNamespace(
        production_date=datetime.combine(day, datetime.min.time()),
        total_yield=litres,
        morning_yield=None,
        afternoon_yield=None,
        evening_yield=None,
        status=status,
    )


def disposition(day, litres, kind="SOLD", status="RECORDED", row_id=1):
    return SimpleNamespace(
        id=row_id,
        production_date=day,
        quantity_litres=litres,
        disposition_type=kind,
        status=status,
    )


def test_overall_saleable_capacity_carries_prior_production_forward():
    factory = Factory(
        [
            production(date(2026, 8, 31), 100.0),
            production(date(2026, 9, 1), 13.0),
        ],
        [disposition(date(2026, 8, 31), 20.0)],
    )

    result = overall_saleable_capacity(date(2026, 9, 1), factory=factory)

    assert result["saleable_production_litres"] == 113.0
    assert result["ordinary_accounted_litres"] == 20.0
    assert result["available_saleable_litres"] == 93.0


def test_overall_saleable_capacity_excludes_withdrawal_and_inactive_rows():
    factory = Factory(
        [
            production(date(2026, 9, 1), 80.0),
            production(date(2026, 9, 1), 20.0, status="WITHDRAWAL"),
            production(date(2026, 9, 1), 500.0, status="VOID"),
        ],
        [
            disposition(date(2026, 9, 1), 30.0, kind="SOLD", row_id=1),
            disposition(date(2026, 9, 1), 15.0, kind="WITHDRAWAL", row_id=2),
            disposition(date(2026, 9, 1), 99.0, kind="SOLD", status="VOID", row_id=3),
        ],
    )

    result = overall_saleable_capacity(date(2026, 9, 1), factory=factory)

    assert result["biological_production_litres"] == 100.0
    assert result["withdrawal_litres"] == 20.0
    assert result["saleable_production_litres"] == 80.0
    assert result["ordinary_accounted_litres"] == 30.0
    assert result["withdrawal_accounted_litres"] == 15.0
    assert result["available_saleable_litres"] == 50.0


def test_edit_can_exclude_existing_disposition_from_capacity():
    existing = disposition(date(2026, 9, 1), 40.0, row_id=7)
    factory = Factory([production(date(2026, 9, 1), 50.0)], [existing])

    ordinary = overall_saleable_capacity(date(2026, 9, 1), factory=factory)
    excluding = overall_saleable_capacity(
        date(2026, 9, 1),
        exclude_disposition_id=7,
        factory=factory,
    )

    assert ordinary["available_saleable_litres"] == 10.0
    assert excluding["available_saleable_litres"] == 50.0
