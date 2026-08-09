from dairyos.intelligence.knowledge.repository.knowledge_pattern_repository import (
    KnowledgePatternRepository,
)


class MemoryKnowledgePatternRepository(
    KnowledgePatternRepository,
):

    def __init__(
        self,
    ):

        self._items = []


    def save(
        self,
        pattern,
    ):

        self._items.append(
            pattern
        )


    def get_all(
        self,
    ):

        return self._items
