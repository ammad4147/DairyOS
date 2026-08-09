from dairyos.intelligence.memory.gateway.memory_gateway import (
    MemoryGateway,
)

from dairyos.intelligence.memory.services.memory_service import (
    MemoryService,
)

from dairyos.intelligence.memory.repository.adapters.memory_memory_repository import (
    MemoryMemoryRepository,
)


def test_memory_gateway_create():

    repository = MemoryMemoryRepository()

    service = MemoryService(
        repository
    )

    gateway = MemoryGateway(
        service
    )

    result = gateway.create_memory(
        "m1",
        "knowledge",
        "test memory",
        "system",
        1.0,
    )

    assert result.memory_id == "m1"
