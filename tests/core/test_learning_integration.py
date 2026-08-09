from dairyos.intelligence.learning.integration.learning_integration import (
    LearningIntegration,
)

from dairyos.intelligence.learning.gateway.learning_gateway import (
    LearningGateway,
)

from dairyos.intelligence.learning.services.learning_service import (
    LearningService,
)

from dairyos.intelligence.learning.repository.adapters.memory_learning_repository import (
    MemoryLearningRepository,
)

from dairyos.intelligence.persistence.models.intelligence_event import (
    IntelligenceEvent,
)


def test_learning_integration_processes_history():

    repository = MemoryLearningRepository()


    service = LearningService(
        repository
    )


    gateway = LearningGateway(
        service
    )


    integration = LearningIntegration(
        gateway
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


    knowledge = integration.process_history(
        events
    )


    assert len(knowledge) == 1


    stored = integration.get_knowledge()


    assert len(stored) == 1


    assert stored[0].category == (
        "operational_risk"
    )
