from dairyos.operations.memory.services.memory_service import (
    MemoryService,
)
from dairyos.operations.memory.services.pattern_learning_service import (
    PatternLearningService,
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
