from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)

from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
    MemoryEventRepository,
)


def test_memory_event_repository_stores_events():

    repository = MemoryEventRepository()


    event = IntelligenceEvent(
        event_type="decision_created",
        source="intelligence_kernel",
        payload={
            "decision": "Inspect animal",
        },
    )


    repository.save_event(
        event
    )


    events = repository.get_events()


    assert len(events) == 1


    assert events[0].event_type == (
        "decision_created"
    )


def test_memory_event_repository_filters_by_type():

    repository = MemoryEventRepository()


    repository.save_event(
        IntelligenceEvent(
            event_type="signal_received",
            source="health",
            payload={},
        )
    )


    repository.save_event(
        IntelligenceEvent(
            event_type="decision_created",
            source="kernel",
            payload={},
        )
    )


    results = repository.find_events_by_type(
        "signal_received"
    )


    assert len(results) == 1


    assert results[0].source == "health"
