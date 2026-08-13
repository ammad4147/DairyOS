"""Unit tests for milking-session sequencing (G3.1).

These exercise the service against the in-memory ledger so the three
restraints -- empty ledger, unobserved AFTERNOON, pre-ledger dates -- can be
tested without a database.
"""

from datetime import date, timedelta

import pytest

from dairyos.data.repositories.milking_session_record_repository import (
    MilkingSessionRecordRepository,
)
from dairyos.milk.models.milking_session_ledger import MilkingSessionStatus
from dairyos.milk.services.milk_session_sequence_service import (
    MilkSessionSequenceService,
    SequenceViolation,
)


DAY = date(2026, 8, 13)


@pytest.fixture()
def ledger():
    return MilkingSessionRecordRepository()


@pytest.fixture()
def sequence(ledger):
    return MilkSessionSequenceService(ledger)


def _settle(ledger, day, session, status=MilkingSessionStatus.RECORDED.value):
    return ledger.settle(
        operational_date=day,
        milking_session=session,
        status=status,
        reason=None if status == MilkingSessionStatus.RECORDED.value else "WEATHER",
    )


# ----------------------------------------------------------------------
# Restraint 1: an empty ledger blocks nothing
# ----------------------------------------------------------------------

def test_empty_ledger_blocks_nothing(sequence):
    sequence.assert_can_record(DAY, "EVENING")

    assert sequence.outstanding_before(DAY, "EVENING") == []


# ----------------------------------------------------------------------
# Restraint 2: AFTERNOON is only sequenced once the farm records one
# ----------------------------------------------------------------------

def test_twice_daily_farm_is_not_blocked_by_an_afternoon_it_never_runs(
    ledger, sequence
):
    _settle(ledger, DAY, "MORNING")

    # A TWICE_DAILY farm goes morning -> evening. The afternoon it has never
    # run must not sit in the way forever.
    sequence.assert_can_record(DAY, "EVENING")
    assert "AFTERNOON" not in sequence.observed_sessions()


def test_afternoon_becomes_sequenced_once_the_farm_records_one(
    ledger, sequence
):
    earlier = DAY - timedelta(days=1)
    _settle(ledger, earlier, "MORNING")
    _settle(ledger, earlier, "AFTERNOON")
    _settle(ledger, earlier, "EVENING")

    _settle(ledger, DAY, "MORNING")

    assert "AFTERNOON" in sequence.observed_sessions()
    assert sequence.outstanding_before(DAY, "EVENING") == ["AFTERNOON"]

    with pytest.raises(SequenceViolation):
        sequence.assert_can_record(DAY, "EVENING")


# ----------------------------------------------------------------------
# Restraint 3: dates before the ledger began are backfill, not disorder
# ----------------------------------------------------------------------

def test_dates_before_the_ledger_started_are_not_sequenced(ledger, sequence):
    _settle(ledger, DAY, "MORNING")

    history = DAY - timedelta(days=30)

    sequence.assert_can_record(history, "EVENING")


# ----------------------------------------------------------------------
# The interlock itself
# ----------------------------------------------------------------------

def test_evening_is_blocked_while_morning_is_outstanding(ledger, sequence):
    _settle(ledger, DAY - timedelta(days=1), "MORNING")

    assert sequence.outstanding_before(DAY, "EVENING") == ["MORNING"]

    with pytest.raises(SequenceViolation) as excinfo:
        sequence.assert_can_record(DAY, "EVENING")

    assert excinfo.value.blocking_session == "MORNING"


def test_morning_is_never_blocked(ledger, sequence):
    _settle(ledger, DAY - timedelta(days=1), "MORNING")

    sequence.assert_can_record(DAY, "MORNING")


def test_a_declared_skip_settles_the_session(ledger, sequence):
    _settle(ledger, DAY - timedelta(days=1), "MORNING")
    _settle(ledger, DAY, "MORNING", MilkingSessionStatus.NOT_MILKED.value)

    # NOT_MILKED is a statement about the session, so the day can proceed.
    sequence.assert_can_record(DAY, "EVENING")


def test_next_outstanding_session_walks_the_day(ledger, sequence):
    assert sequence.next_outstanding_session(DAY) == "MORNING"

    _settle(ledger, DAY, "MORNING")
    assert sequence.next_outstanding_session(DAY) == "EVENING"

    _settle(ledger, DAY, "EVENING")
    assert sequence.next_outstanding_session(DAY) is None


# ----------------------------------------------------------------------
# The refusal has to be actionable
# ----------------------------------------------------------------------

def test_operator_guidance_names_both_routes_forward(ledger, sequence):
    _settle(ledger, DAY - timedelta(days=1), "MORNING")

    with pytest.raises(SequenceViolation) as excinfo:
        sequence.assert_can_record(DAY, "EVENING")

    guidance = excinfo.value.as_operator_guidance()

    assert guidance["error"] == "MILKING_SESSION_OUT_OF_SEQUENCE"
    assert guidance["next_session"] == "MORNING"
    assert guidance["operational_date"] == DAY.isoformat()

    actions = {item["action"] for item in guidance["resolutions"]}
    assert actions == {"RECORD_SESSION", "DECLARE_NOT_MILKED"}

    endpoints = {item["endpoint"] for item in guidance["resolutions"]}
    assert "POST /farm/milk" in endpoints
    assert "POST /farm/milk/not-milked" in endpoints


# ----------------------------------------------------------------------
# Ledger identity and idempotence
# ----------------------------------------------------------------------

def test_session_record_ids_are_sequential_per_day(ledger):
    first = _settle(ledger, DAY, "MORNING")
    second = _settle(ledger, DAY, "EVENING")

    assert first.session_record_id == "MS-260813-001"
    assert second.session_record_id == "MS-260813-002"


def test_settling_twice_keeps_the_first_statement(ledger):
    first = _settle(ledger, DAY, "MORNING")
    again = _settle(ledger, DAY, "MORNING")

    assert again is first
    assert ledger.count() == 1


def test_ledger_rejects_nothing_it_has_not_been_told_about(ledger):
    assert ledger.get_for(DAY, "MORNING") is None
    assert ledger.settled_sessions_on(DAY) == set()
    assert ledger.has_session_ever("AFTERNOON") is False
