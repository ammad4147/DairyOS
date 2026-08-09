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


def test_complete_intelligence_learning_flow():

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
            source="herd_health",
            payload={
                "severity": "critical",
                "category": "animal_health",
            },
        ),

        IntelligenceEvent(
            event_type="signal_received",
            source="herd_health",
            payload={
                "severity": "critical",
                "category": "animal_health",
            },
        ),

    ]


    learned = integration.process_history(
        events
    )


    assert len(learned) == 1


    signal = learned[0]


    assert signal.category == (
        "operational_risk"
    )


    assert signal.confidence > 0


    knowledge = integration.get_knowledge()


    assert len(knowledge) == 1


    assert knowledge[0].description == (
        "Critical intelligence events detected in history"
    )
