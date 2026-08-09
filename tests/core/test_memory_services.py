from dairyos.intelligence.memory.services.memory_service import (
    MemoryService,
)

from dairyos.intelligence.memory.services.context_manager import (
    ContextManager,
)

from dairyos.intelligence.memory.services.memory_retrieval_service import (
    MemoryRetrievalService,
)

from dairyos.intelligence.memory.services.memory_consolidation_service import (
    MemoryConsolidationService,
)

from dairyos.intelligence.memory.repository.adapters.memory_memory_repository import (
    MemoryMemoryRepository,
)

from dairyos.intelligence.memory.repository.adapters.memory_context_repository import (
    MemoryContextRepository,
)


def test_memory_service_create():

    repository = MemoryMemoryRepository()

    service = MemoryService(
        repository
    )

    result = service.create(
        "m1",
        "operational",
        "test",
        "system",
        0.9,
    )

    assert result.memory_id == "m1"



def test_context_manager_create():

    repository = MemoryContextRepository()

    service = ContextManager(
        repository
    )

    result = service.create(
        "c1",
        "farm",
        "test",
        "system",
    )

    assert result.context_id == "c1"



def test_memory_retrieval():

    repository = MemoryMemoryRepository()

    service = MemoryRetrievalService(
        repository
    )

    assert service.retrieve_all() == []



def test_memory_consolidation():

    repository = MemoryMemoryRepository()

    service = MemoryConsolidationService(
        repository
    )

    assert service.consolidate() == 0
