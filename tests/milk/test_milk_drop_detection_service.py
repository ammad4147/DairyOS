from datetime import date
from types import SimpleNamespace

from dairyos.farm.herd.services.animal_milking_schedule_service import AnimalMilkingScheduleService
from dairyos.farm.production.services.milk_drop_detection_service import detect_drop


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


def _row(day, morning, afternoon, evening):
    return {
        "animal_id": "TD-001",
        "production_date": day,
        "session_ledger": True,
        "status": "RECORDED",
        "morning_yield": morning,
        "afternoon_yield": afternoon,
        "evening_yield": evening,
        "total_yield": None,
    }


def test_drop_uses_immediately_preceding_production_date_not_calendar_yesterday():
    animal = SimpleNamespace(animal_id="TD-001", milking_frequency="THRICE_DAILY")
    history = [_history("TD-001", "THRICE_DAILY", date(2026, 8, 1))]
    schedule = AnimalMilkingScheduleService(FakeRepository(history))
    records = [
        _row(date(2026, 8, 10), 10.0, 10.0, 10.0),
        _row(date(2026, 8, 12), 8.0, 8.0, 8.0),
    ]

    result = detect_drop(
        records,
        animal_id="TD-001",
        as_of_date=date(2026, 8, 12),
        schedule_service=schedule,
        animal=animal,
    )

    assert result["status"] == "COMPLETE"
    assert result["previous_date"] == "2026-08-10"
    assert result["previous"] == 30.0
    assert result["current"] == 24.0
    assert result["percent"] == -20.0


def test_drop_resolves_previous_frequency_for_previous_production_date():
    animal = SimpleNamespace(animal_id="TD-002", milking_frequency="THRICE_DAILY")
    history = [
        _history("TD-002", "TWICE_DAILY", date(2026, 8, 1), date(2026, 8, 12)),
        _history("TD-002", "THRICE_DAILY", date(2026, 8, 12)),
    ]
    schedule = AnimalMilkingScheduleService(FakeRepository(history))
    records = [
        {
            "animal_id": "TD-002", "production_date": date(2026, 8, 11),
            "session_ledger": True, "status": "RECORDED",
            "morning_yield": 15.0, "afternoon_yield": None,
            "evening_yield": 15.0, "total_yield": None,
        },
        _row(date(2026, 8, 12), 10.0, 10.0, 10.0) | {"animal_id": "TD-002"},
    ]

    result = detect_drop(
        records,
        animal_id="TD-002",
        as_of_date=date(2026, 8, 12),
        schedule_service=schedule,
        animal=animal,
    )

    assert result["status"] == "COMPLETE"
    assert result["previous_date"] == "2026-08-11"
    assert result["previous"] == 30.0
    assert result["current"] == 30.0
    assert result["percent"] == 0.0
