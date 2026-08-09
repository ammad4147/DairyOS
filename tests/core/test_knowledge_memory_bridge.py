from dairyos.intelligence.memory.integration.knowledge_memory_bridge import (
    KnowledgeMemoryBridge,
)

from dairyos.intelligence.memory.gateway.memory_gateway import (
    MemoryGateway,
)

from dairyos.intelligence.memory.services.memory_service import (
    MemoryService,
)

from dairyos.intelligence.memory.repository.adapters.memory_memory_repository import (
    MemoryMemoryRepository,
)


def test_knowledge_memory_bridge():

    repository = MemoryMemoryRepository()

    service = MemoryService(
        repository
    )

    gateway = MemoryGateway(
        service
    )

    bridge = KnowledgeMemoryBridge(
        gateway
    )

    result = bridge.store_knowledge_memory(
        "m1",
        "knowledge item",
    )

    assert result.memory_id == "m1"
