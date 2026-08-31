from datetime import date
from types import SimpleNamespace

import pytest

from dairyos.data.repositories.milking_session_record_repository import (
    MilkingSessionRecordRepository,
)
from dairyos.milk.services.milk_session_sequence_service import (
    MilkSessionSequenceService,
    SequenceViolation,
)


DAY = date(2026, 8, 31)


class MilkRows:
    def __init__(self):
        self.rows = {}

    def ledger_row_for_animal_day(self, animal_id, production_day):
        return self.rows.get((animal_id, production_day))


class Schedules:
    def get_expected_sessions(self, animal, operational_date):
        if animal.milking_frequency == "THRICE_DAILY":
            return ("MORNING", "AFTERNOON", "EVENING")
        return ("MORNING", "EVENING")


def row(animal_id, *, morning=None, afternoon=None, evening=None, status="RECORDED"):
    return SimpleNamespace(
        animal_id=animal_id,
        morning_yield=morning,
        afternoon_yield=afternoon,
        evening_yield=evening,
        status=status,
    )


@pytest.fixture()
def authority():
    ledger = MilkingSessionRecordRepository()
    milk = MilkRows()
    service = MilkSessionSequenceService(
        ledger,
        schedule_service=Schedules(),
        milk_repository=milk,
    )
    return ledger, milk, service


def test_other_animals_do_not_advance_td002_session(authority):
    ledger, milk, service = authority
    td002 = SimpleNamespace(animal_id="TD-002", milking_frequency="TWICE_DAILY")

    ledger.settle(
        operational_date=DAY,
        milking_session="MORNING",
        status="RECORDED",
    )
    ledger.settle(
        operational_date=DAY,
        milking_session="EVENING",
        status="RECORDED",
    )
    milk.rows[("TD-002", DAY)] = row("TD-002", morning=10.0)

    assert service.settled_sessions_on(DAY, animal=td002) == ["MORNING"]
    service.assert_can_record(DAY, "EVENING", animal=td002)


def test_twice_daily_rejects_afternoon_and_duplicate(authority):
    _, milk, service = authority
    td002 = SimpleNamespace(animal_id="TD-002", milking_frequency="TWICE_DAILY")
    milk.rows[("TD-002", DAY)] = row("TD-002", morning=10.0)

    with pytest.raises(SequenceViolation) as unscheduled:
        service.assert_can_record(DAY, "AFTERNOON", animal=td002)
    assert unscheduled.value.reason == "UNSCHEDULED_SESSION"

    with pytest.raises(SequenceViolation) as duplicate:
        service.assert_can_record(DAY, "MORNING", animal=td002)
    assert duplicate.value.reason == "SESSION_ALREADY_SETTLED"


def test_thrice_daily_accepts_exactly_three_sessions(authority):
    _, milk, service = authority
    animal = SimpleNamespace(animal_id="TD-003", milking_frequency="THRICE_DAILY")

    milk.rows[("TD-003", DAY)] = row("TD-003", morning=10.0)
    service.assert_can_record(DAY, "AFTERNOON", animal=animal)

    milk.rows[("TD-003", DAY)] = row("TD-003", morning=10.0, afternoon=10.0)
    service.assert_can_record(DAY, "EVENING", animal=animal)

    milk.rows[("TD-003", DAY)] = row(
        "TD-003", morning=10.0, afternoon=10.0, evening=10.0
    )
    for session in ("MORNING", "AFTERNOON", "EVENING"):
        with pytest.raises(SequenceViolation) as duplicate:
            service.assert_can_record(DAY, session, animal=animal)
        assert duplicate.value.reason == "SESSION_ALREADY_SETTLED"


def test_voided_day_reopens_authorized_sessions(authority):
    _, milk, service = authority
    animal = SimpleNamespace(animal_id="TD-002", milking_frequency="TWICE_DAILY")
    milk.rows[("TD-002", DAY)] = row(
        "TD-002", morning=10.0, evening=10.0, status="VOID"
    )

    assert service.settled_sessions_on(DAY, animal=animal) == []
    service.assert_can_record(DAY, "MORNING", animal=animal)


def test_farm_not_milked_settles_session_for_every_animal(authority):
    ledger, _, service = authority
    animal = SimpleNamespace(animal_id="TD-002", milking_frequency="TWICE_DAILY")
    ledger.settle(
        operational_date=DAY,
        milking_session="MORNING",
        status="NOT_MILKED",
        reason="EQUIPMENT_FAILURE",
    )

    assert service.settled_sessions_on(DAY, animal=animal) == ["MORNING"]
    service.assert_can_record(DAY, "EVENING", animal=animal)
