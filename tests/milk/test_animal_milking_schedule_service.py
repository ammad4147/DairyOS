from datetime import date, datetime
from types import SimpleNamespace

from dairyos.farm.production.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)


class FakeRepository:
    def __init__(self, history):
        self.history = history

    def get_milking_frequency_history(self, animal_id):
        return self.history


def _history(animal_id, frequency, effective_from, effective_to=None):
    return SimpleNamespace(
        id=1,
        animal_id=animal_id,
        milking_frequency=frequency,
        effective_from=effective_from,
        effective_to=effective_to,
        changed_by="operator",
        reason="test",
    )


def test_resolves_historical_frequency_from_effective_date():
    animal = SimpleNamespace(animal_id="TD-001", milking_frequency="THRICE_DAILY")
    history = [
        _history(
            "TD-001",
            "THRICE_DAILY",
            datetime(2026, 8, 10, 8, 0),
            datetime(2026, 8, 15, 9, 0),
        ),
        _history(
            "TD-001",
            "TWICE_DAILY",
            datetime(2026, 8, 15, 9, 0),
        ),
    ]
    service = AnimalMilkingScheduleService(FakeRepository(history))

    assert service.get_frequency_for_date(animal, date(2026, 8, 12)) == "THRICE_DAILY"
    assert service.get_frequency_for_date(animal, date(2026, 8, 16)) == "TWICE_DAILY"


def test_expected_sessions_are_derived_from_resolved_frequency():
    animal = SimpleNamespace(animal_id="TD-002", milking_frequency="TWICE_DAILY")
    history = [_history("TD-002", "THRICE_DAILY", datetime(2026, 8, 1, 8, 0))]
    service = AnimalMilkingScheduleService(FakeRepository(history))

    assert service.get_expected_sessions(animal, date(2026, 8, 2)) == (
        "MORNING",
        "AFTERNOON",
        "EVENING",
    )


def test_current_frequency_is_not_used_for_history_when_history_exists():
    animal = SimpleNamespace(animal_id="TD-003", milking_frequency="THRICE_DAILY")
    history = [_history("TD-003", "TWICE_DAILY", datetime(2026, 8, 10, 8, 0))]
    service = AnimalMilkingScheduleService(FakeRepository(history))

    assert service.get_frequency_for_date(animal, date(2026, 8, 9)) is None


def test_current_frequency_fallback_is_used_only_without_history():
    animal = SimpleNamespace(animal_id="TD-004", milking_frequency="TWICE_DAILY")
    service = AnimalMilkingScheduleService(FakeRepository([]))

    assert service.get_frequency_for_date(animal, date(2020, 1, 1)) == "TWICE_DAILY"
    assert service.get_expected_sessions(animal, date(2020, 1, 1)) == (
        "MORNING",
        "EVENING",
    )


def test_snapshot_exposes_historical_provenance():
    animal = SimpleNamespace(animal_id="TD-005", milking_frequency="TWICE_DAILY")
    history = [
        _history("TD-005", "THRICE_DAILY", datetime(2026, 8, 10, 8, 0))
    ]
    service = AnimalMilkingScheduleService(FakeRepository(history))

    snapshot = service.get_schedule_snapshot(animal, date(2026, 8, 11))

    assert snapshot.source == "SCHEDULE_HISTORY"
    assert snapshot.milking_frequency == "THRICE_DAILY"
    assert snapshot.expected_sessions == (
        "MORNING",
        "AFTERNOON",
        "EVENING",
    )
    assert snapshot.changed_by == "operator"
    assert snapshot.reason == "test"
