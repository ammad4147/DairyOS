from dairyos.intelligence.learning.services.learning_service import (
    LearningService,
)

from dairyos.intelligence.learning.repository.adapters.memory_learning_repository import (
    MemoryLearningRepository,
)

from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)


def test_learning_service_creates_and_stores_learning_signal():

    repository = MemoryLearningRepository()


    service = LearningService(
        repository
    )


    events = [
        IntelligenceEvent(
            event_type="signal_received",
            source="health",
            payload={
                "severity": "critical",
            },
        )
    ]


    signals = service.learn(
        events
    )


    assert len(signals) == 1


    stored = (
        service.get_learning_signals()
    )


    assert len(stored) == 1


    assert stored[0].category == (
        "operational_risk"
    )


def test_learning_service_returns_empty_for_no_patterns():

    repository = MemoryLearningRepository()


    service = LearningService(
        repository
    )


    signals = service.learn(
        []
    )


    assert len(signals) == 0


    assert (
        len(
            service.get_learning_signals()
        )
        == 0
    )
