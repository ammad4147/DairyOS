from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)

from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
    MemoryEventRepository,
)

from dairyos.intelligence.persistence.services.history.intelligence_history_service import (
    IntelligenceHistoryService,
)


def test_history_service_returns_event_history():

    repository = MemoryEventRepository()


    repository.save_event(
        IntelligenceEvent(
            event_type="signal_received",
            source="health",
            payload={
                "severity": "critical",
            },
        )
    )


    repository.save_event(
        IntelligenceEvent(
            event_type="decision_created",
            source="kernel",
            payload={
                "decision": "Inspect animal",
            },
        )
    )


    service = IntelligenceHistoryService(
        repository
    )


    history = service.get_history()


    assert len(history) == 2


    assert history[0].event_type == (
        "signal_received"
    )


def test_history_service_filters_event_types():

    repository = MemoryEventRepository()


    repository.save_event(
        IntelligenceEvent(
            event_type="decision_created",
            source="kernel",
            payload={},
        )
    )


    repository.save_event(
        IntelligenceEvent(
            event_type="signal_received",
            source="health",
            payload={},
        )
    )


    service = IntelligenceHistoryService(
        repository
    )


    decisions = (
        service.get_events_by_type(
            "decision_created"
        )
    )


    assert len(decisions) == 1


    timeline = (
        service.get_decision_timeline()
    )


    assert len(timeline) == 1
