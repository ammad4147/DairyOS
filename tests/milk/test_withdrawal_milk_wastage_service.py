from datetime import date, datetime, timezone
from types import SimpleNamespace

from dairyos.farm.production.services.withdrawal_milk_wastage_service import (
    AUTO_WASTAGE_PREFIX,
    animal_withdrawn_on_date,
    ensure_withdrawal_wastage,
)


class _DispositionRepo:
    def __init__(self):
        self.rows = []

    def get_by_date(self, day):
        return [row for row in self.rows if row.production_date == day]

    def add(self, item):
        item.id = len(self.rows) + 1
        self.rows.append(item)
        return item


class _Factory:
    def __init__(self):
        self.repo = _DispositionRepo()

    def milk_dispositions(self):
        return self.repo


class _WithdrawalService:
    def __init__(self, periods):
        self.periods = periods

    def get_periods_for_animal(self, animal_id):
        return [p for p in self.periods if p.animal_id == animal_id]


def test_withdrawal_overlap_is_date_aware():
    service = _WithdrawalService([
        SimpleNamespace(
            animal_id="TD-001",
            start_time=datetime(2026, 9, 2, 10, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 5, 10, tzinfo=timezone.utc),
        )
    ])

    assert animal_withdrawn_on_date(service, "TD-001", date(2026, 9, 2))
    assert animal_withdrawn_on_date(service, "TD-001", date(2026, 9, 5))
    assert not animal_withdrawn_on_date(service, "TD-001", date(2026, 9, 6))


def test_withdrawal_milk_creates_idempotent_wastage_disposition():
    factory = _Factory()
    service = _WithdrawalService([
        SimpleNamespace(
            animal_id="TD-001",
            start_time=datetime(2026, 9, 1, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 4, tzinfo=timezone.utc),
        )
    ])

    first = ensure_withdrawal_wastage(
        repository_factory=factory,
        withdrawal_service=service,
        animal_id="TD-001",
        production_date=date(2026, 9, 2),
        milking_session="MORNING",
        quantity_litres=10.0,
        recorded_by="Operator",
    )
    second = ensure_withdrawal_wastage(
        repository_factory=factory,
        withdrawal_service=service,
        animal_id="TD-001",
        production_date=date(2026, 9, 2),
        milking_session="MORNING",
        quantity_litres=10.0,
        recorded_by="Operator",
    )

    assert first is second
    assert len(factory.repo.rows) == 1
    assert first.disposition_type == "WASTAGE"
    assert first.quantity_litres == 10.0
    assert AUTO_WASTAGE_PREFIX in first.notes
