from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
    MemoryEventRepository,
)

from dairyos.intelligence.persistence.services.event_recorder import (
    EventRecorder,
)


def test_event_recorder_creates_history_event():

    repository = MemoryEventRepository()


    recorder = EventRecorder(
        repository
    )


    event = recorder.record(
        event_type="signal_received",
        source="animal_health",
        payload={
            "severity": "critical",
            "message": "Temperature alert",
        },
    )


    assert event.event_type == (
        "signal_received"
    )


    assert event.source == (
        "animal_health"
    )


    assert event.payload["severity"] == (
        "critical"
    )


    stored_events = (
        repository.get_events()
    )


    assert len(stored_events) == 1


    assert stored_events[0].event_id == (
        event.event_id
    )
