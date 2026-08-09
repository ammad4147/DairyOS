from dairyos.intelligence.learning_feedback.repository.knowledge_repository import (
    KnowledgeRepository,
)


class MemoryKnowledgeRepository(
    KnowledgeRepository,
):

    def __init__(
        self,
    ):

        self._items = []


    def save(
        self,
        knowledge,
    ):

        self._items.append(
            knowledge,
        )


    def get_all(
        self,
    ):

        return self._items
