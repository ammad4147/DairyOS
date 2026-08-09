from dairyos.intelligence.learning_feedback.repository.score_repository import (
    ScoreRepository,
)


class MemoryScoreRepository(
    ScoreRepository,
):

    def __init__(
        self,
    ):

        self._items = []


    def save(
        self,
        score,
    ):

        self._items.append(
            score,
        )


    def get_all(
        self,
    ):

        return self._items
