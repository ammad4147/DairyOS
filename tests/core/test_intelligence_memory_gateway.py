from dairyos.intelligence.persistence.gateway.intelligence_memory_gateway import (
    IntelligenceMemoryGateway,
)

from dairyos.intelligence.persistence.repositories.adapters.memory_event_repository import (
    MemoryEventRepository,
)


def test_memory_gateway_records_and_reads_history():

    repository = MemoryEventRepository()


    gateway = IntelligenceMemoryGateway(
        repository
    )


    gateway.record(
        event_type="decision_created",
        source="intelligence_kernel",
        payload={
            "decision": "Inspect animal",
        },
    )


    history = gateway.get_history()


    assert len(history) == 1


    assert history[0].event_type == (
        "decision_created"
    )


    assert history[0].source == (
        "intelligence_kernel"
    )


def test_memory_gateway_returns_decision_timeline():

    repository = MemoryEventRepository()


    gateway = IntelligenceMemoryGateway(
        repository
    )


    gateway.record(
        event_type="decision_created",
        source="kernel",
        payload={},
    )


    gateway.record(
        event_type="signal_received",
        source="health",
        payload={},
    )


    timeline = gateway.get_decision_timeline()


    assert len(timeline) == 1


    assert timeline[0].event_type == (
        "decision_created"
    )
