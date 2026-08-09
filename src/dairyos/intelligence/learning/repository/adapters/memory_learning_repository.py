from dairyos.intelligence.learning.repository.learning_repository import (
    LearningRepository,
)

from dairyos.intelligence.learning.models.learning_signal import (
    LearningSignal,
)


class MemoryLearningRepository(
    LearningRepository
):
    """
    In-memory learning signal storage.

    Used for:

    - testing
    - development
    - future adapter validation
    """


    def __init__(
        self,
    ):

        self.signals = []


    def save(
        self,
        signal: LearningSignal,
    ):

        self.signals.append(
            signal
        )


    def get_all(
        self,
    ) -> list[LearningSignal]:

        return self.signals
