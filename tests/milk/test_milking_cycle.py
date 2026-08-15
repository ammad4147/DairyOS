from datetime import date, datetime, timezone

import pytest

from dairyos.farm.operations.state.operational_schedule_state import OperationalScheduleState
from dairyos.milk.models.milking_cycle import MilkingCycle, MilkingFrequency


def test_cycle_accepts_only_two_or_three_sessions():
    assert MilkingCycle("A1", MilkingFrequency.TWICE_DAILY, date(2026, 8, 15)).sessions == ["MORNING", "EVENING"]
    assert MilkingCycle("A2", MilkingFrequency.THREE_TIMES_DAILY, date(2026, 8, 15)).sessions == ["MORNING", "AFTERNOON", "EVENING"]
    with pytest.raises(ValueError):
        MilkingCycle("A3", 4, date(2026, 8, 15))


def test_schedule_generates_date_specific_expected_sessions_per_animal():
    state = OperationalScheduleState("2026-08-15")
    state.configure_milking_cycle("A1", 2, "2026-08-15")
    state.configure_milking_cycle("A2", 3, "2026-08-15")
    generated = state.schedule_milking_cycles_for_date("2026-08-15")
    assert len(generated) == 5
    assert {item["animal_id"] for item in generated} == {"A1", "A2"}
    assert all(item["operational_date"] == "2026-08-15" for item in generated)


def test_future_date_does_not_materialise_before_effective_date():
    state = OperationalScheduleState("2026-08-14")
    state.configure_milking_cycle("A1", 2, "2026-08-15")
    assert state.schedule_milking_cycles_for_date("2026-08-14") == []
    assert len(state.schedule_milking_cycles_for_date("2026-08-15")) == 2


def test_missed_session_remains_pending_until_explicit_outcome():
    state = OperationalScheduleState("2026-08-15")
    state.configure_milking_cycle("A1", 2, "2026-08-15")
    state.schedule_milking_cycles_for_date("2026-08-15")
    assert len(state.pending_milk_sessions("A1", "2026-08-15")) == 2
    state.record_milking_session("A1", "2026-08-15", "MORNING", "RECORDED", recorded_at=datetime(2026, 8, 15, 6, 10, tzinfo=timezone.utc))
    assert len(state.pending_milk_sessions("A1", "2026-08-15")) == 1


def test_not_milked_requires_reason():
    state = OperationalScheduleState("2026-08-15")
    state.configure_milking_cycle("A1", 2, "2026-08-15")
    state.schedule_milking_cycles_for_date("2026-08-15")
    with pytest.raises(ValueError):
        state.record_milking_session("A1", "2026-08-15", "MORNING", "NOT_MILKED")
    outcome = state.record_milking_session("A1", "2026-08-15", "MORNING", "NOT_MILKED", reason="POWER_OUTAGE")
    assert outcome["status"] == "NOT_MILKED"


def test_late_entry_is_flagged_against_scheduled_time():
    state = OperationalScheduleState("2026-08-15")
    state.configure_milking_cycle("A1", 2, "2026-08-15")
    state.schedule_milking_cycles_for_date("2026-08-15")
    outcome = state.record_milking_session(
        "A1", "2026-08-15", "MORNING", "RECORDED",
        recorded_at=datetime(2026, 8, 15, 7, 0, tzinfo=timezone.utc),
    )
    assert outcome["late"] is True


def test_completed_date_requires_all_expected_sessions():
    state = OperationalScheduleState("2026-08-15")
    state.configure_milking_cycle("A1", 2, "2026-08-15")
    state.schedule_milking_cycles_for_date("2026-08-15")
    assert state.is_milking_date_complete("2026-08-15") is False
    state.record_milking_session("A1", "2026-08-15", "MORNING", "RECORDED")
    assert state.is_milking_date_complete("2026-08-15") is False
    state.record_milking_session("A1", "2026-08-15", "EVENING", "NOT_MILKED", reason="POWER_OUTAGE")
    assert state.is_milking_date_complete("2026-08-15") is True
