from dairyos.intelligence.learning_feedback.repository.learning_feedback_repository import (
    LearningFeedbackRepository,
)


class MemoryLearningFeedbackRepository(
    LearningFeedbackRepository,
):

    def __init__(
        self,
    ):

        self._items = []


    def save(
        self,
        feedback,
    ):

        self._items.append(
            feedback,
        )


    def get_all(
        self,
    ):

        return self._items
