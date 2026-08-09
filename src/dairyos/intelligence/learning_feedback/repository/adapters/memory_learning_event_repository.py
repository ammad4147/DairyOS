from dairyos.intelligence.learning_feedback.repository.learning_event_repository import (
    LearningEventRepository,
)


class MemoryLearningEventRepository(
    LearningEventRepository,
):

    def __init__(
        self,
    ):

        self._items = []


    def save(
        self,
        event,
    ):

        self._items.append(
            event,
        )


    def get_all(
        self,
    ):

        return self._items
