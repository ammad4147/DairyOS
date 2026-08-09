from dairyos.operations.memory.services.memory_service import (
    MemoryService,
)

from dairyos.operations.memory.services.pattern_learning_service import (
    PatternLearningService,
)

from dairyos.operations.memory.services.knowledge_retrieval_service import (
    KnowledgeRetrievalService,
)


def test_store_memory():

    pattern = PatternLearningService().create_pattern(
        category="Feed",
        situation="Supplier delay",
        response="Use backup supplier",
        confidence=0.9,
    )

    memory = MemoryService().store(pattern)

    assert memory.pattern.category == "Feed"


def test_retrieve_memory():

    service = MemoryService()

    pattern = PatternLearningService().create_pattern(
        category="Health",
        situation="Animal illness",
        response="Veterinary review",
    )

    service.store(pattern)

    results = KnowledgeRetrievalService().search(
        service.get_all(),
        "Health",
    )

    assert len(results) == 1

