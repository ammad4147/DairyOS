from dairyos.intelligence.knowledge.integration.learning_knowledge_bridge import (
    LearningKnowledgeBridge,
)

from dairyos.intelligence.knowledge.gateway.knowledge_gateway import (
    KnowledgeGateway,
)

from dairyos.intelligence.knowledge.services.knowledge_service import (
    KnowledgeService,
)

from dairyos.intelligence.knowledge.repository.adapters.memory_knowledge_record_repository import (
    MemoryKnowledgeRecordRepository,
)



def test_learning_knowledge_bridge():

    repository = MemoryKnowledgeRecordRepository()

    service = KnowledgeService(
        repository
    )

    gateway = KnowledgeGateway(
        service
    )

    bridge = LearningKnowledgeBridge(
        gateway
    )

    result = bridge.convert_learning(
        "improved feeding pattern"
    )

    assert result.source == "learning_engine"

    assert result.knowledge_type == "learning_feedback"
