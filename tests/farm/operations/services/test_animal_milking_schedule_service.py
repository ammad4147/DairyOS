from datetime import date, datetime, timezone
from types import SimpleNamespace

from dairyos.farm.herd.services.animal_milking_schedule_service import (
    AnimalMilkingScheduleService,
)


def _animal(
    frequency="THRICE_DAILY",
):
    return SimpleNamespace(
        animal_id="AUDIT-001",
        milking_frequency=frequency,
    )


def _history():
    return [
        SimpleNamespace(
            milking_frequency="THRICE_DAILY",
            effective_from=datetime(
                2026,
                8,
                20,
                tzinfo=timezone.utc,
            ),
            effective_to=None,
        ),
        SimpleNamespace(
            milking_frequency="TWICE_DAILY",
            effective_from=datetime(
                2026,
                8,
                15,
                tzinfo=timezone.utc,
            ),
            effective_to=datetime(
                2026,
                8,
                20,
                tzinfo=timezone.utc,
            ),
        ),
    ]


def test_current_call_without_date_preserves_existing_behavior():
    service = AnimalMilkingScheduleService()

    assert service.get_expected_sessions(
        _animal("THRICE_DAILY")
    ) == [
        "MORNING",
        "AFTERNOON",
        "EVENING",
    ]


def test_historical_date_uses_frequency_effective_on_that_date():
    service = AnimalMilkingScheduleService()

    assert service.get_expected_sessions(
        _animal("THRICE_DAILY"),
        operational_date=date(2026, 8, 18),
        history=_history(),
    ) == [
        "MORNING",
        "EVENING",
    ]


def test_change_date_uses_new_frequency():
    service = AnimalMilkingScheduleService()

    assert service.get_expected_sessions(
        _animal("THRICE_DAILY"),
        operational_date=date(2026, 8, 20),
        history=_history(),
    ) == [
        "MORNING",
        "AFTERNOON",
        "EVENING",
    ]


def test_date_before_history_falls_back_to_current_frequency():
    service = AnimalMilkingScheduleService()

    assert service.get_expected_sessions(
        _animal("THRICE_DAILY"),
        operational_date=date(2026, 8, 10),
        history=_history(),
    ) == [
        "MORNING",
        "AFTERNOON",
        "EVENING",
    ]


def test_effective_to_is_exclusive():
    service = AnimalMilkingScheduleService()

    history = [
        SimpleNamespace(
            milking_frequency="THRICE_DAILY",
            effective_from=datetime(
                2026,
                8,
                20,
                tzinfo=timezone.utc,
            ),
            effective_to=None,
        ),
        SimpleNamespace(
            milking_frequency="TWICE_DAILY",
            effective_from=datetime(
                2026,
                8,
                15,
                tzinfo=timezone.utc,
            ),
            effective_to=datetime(
                2026,
                8,
                20,
                tzinfo=timezone.utc,
            ),
        ),
    ]

    assert service.get_frequency_for_date(
        _animal("THRICE_DAILY"),
        operational_date=date(2026, 8, 20),
        history=history,
    ) == "THRICE_DAILY"


def test_repository_history_is_used_when_no_history_argument_is_supplied():
    history = _history()

    class Repository:
        def get_milking_frequency_history(self, animal_id):
            assert animal_id == "AUDIT-001"
            return history

    service = AnimalMilkingScheduleService(
        repository=Repository()
    )

    assert service.get_expected_sessions(
        _animal("THRICE_DAILY"),
        operational_date=date(2026, 8, 18),
    ) == [
        "MORNING",
        "EVENING",
    ]


def test_string_operational_date_is_supported():
    service = AnimalMilkingScheduleService()

    assert service.get_frequency_for_date(
        _animal("THRICE_DAILY"),
        operational_date="2026-08-18",
        history=_history(),
    ) == "TWICE_DAILY"


def test_schedule_snapshot_reports_date_aware_schedule():
    service = AnimalMilkingScheduleService()

    snapshot = service.get_schedule_snapshot(
        _animal("THRICE_DAILY"),
        operational_date=date(2026, 8, 18),
        history=_history(),
    )

    assert snapshot["operational_date"] == "2026-08-18"
    assert snapshot["milking_frequency"] == "TWICE_DAILY"
    assert snapshot["expected_sessions"] == [
        "MORNING",
        "EVENING",
    ]
