from datetime import datetime, timezone

from dairyos.domain.events import Event
from dairyos.domain.events.operational_input_received import (
    OperationalInputReceived,
)
from dairyos.runtime.journal_entry import JournalEntry


def test_journal_entry_preserves_operational_event_identity():
    event = OperationalInputReceived(
        input_type="milk_production",
        payload={
            "animal_id": "A001",
            "litres": 24.5,
        },
        source="farm_operator",
        actor="worker-01",
    )

    entry = JournalEntry.from_event(
        event
    )

    assert entry.event_id == event.event_id
    assert entry.event_type == "OperationalInputReceived"
    assert entry.payload["animal_id"] == "A001"


def test_journal_entry_preserves_datetime_timestamp():
    timestamp = datetime(
        2026,
        8,
        8,
        12,
        30,
        tzinfo=timezone.utc,
    )

    event = Event(
        name="TestEvent",
        payload={
            "value": 10,
        },
        timestamp=timestamp.isoformat(),
    )

    entry = JournalEntry.from_event(
        event
    )

    assert entry.timestamp == timestamp


def test_journal_entry_generates_identity_for_generic_event():
    event = Event(
        name="TestEvent",
        payload={
            "value": 10,
        },
    )

    entry = JournalEntry.from_event(
        event
    )

    assert entry.event_id
    assert entry.event_type == "TestEvent"
    assert entry.payload["value"] == 10
