from dairyos.intelligence.knowledge.gateway.knowledge_gateway import (
    KnowledgeGateway,
)

from dairyos.intelligence.knowledge.services.knowledge_service import (
    KnowledgeService,
)

from dairyos.intelligence.knowledge.repository.adapters.memory_knowledge_record_repository import (
    MemoryKnowledgeRecordRepository,
)



def test_gateway_create():

    repository = MemoryKnowledgeRecordRepository()

    service = KnowledgeService(
        repository
    )

    gateway = KnowledgeGateway(
        service
    )

    result = gateway.create(
        "pattern",
        "milk trend",
        "learning",
        0.9,
    )

    assert result.content == "milk trend"
