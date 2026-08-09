from dairyos.intelligence.services.intelligence_service import (
    IntelligenceService,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
    MemoryEventRepository,
)


def test_intelligence_service_records_audit_events():

    event_repository = MemoryEventRepository()


    service = IntelligenceService(
        event_repository=event_repository,
    )


    service.submit_signal(
        IntelligenceSignal(
            source="health",
            category="animal_health",
            message="Critical temperature alert",
            severity="critical",
        )
    )


    service.process()


    events = event_repository.get_events()


    assert len(events) >= 2


    assert events[0].event_type == (
        "signal_received"
    )


    assert events[0].source == (
        "health"
    )


    assert events[1].event_type == (
        "intelligence_processed"
    )


    assert events[1].source == (
        "intelligence_service"
    )
