from dairyos.intelligence.learning_feedback.repository.memory_repository import (
    MemoryRepository,
)


class MemoryLearningMemoryRepository(
    MemoryRepository,
):

    def __init__(
        self,
    ):

        self._items = []


    def save(
        self,
        memory,
    ):

        self._items.append(
            memory,
        )


    def get_all(
        self,
    ):

        return self._items
