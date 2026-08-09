from abc import ABC, abstractmethod

from dairyos.intelligence.learning.models.learning_signal import (
    LearningSignal,
)


class LearningRepository(ABC):
    """
    Persistence contract for intelligence learning signals.
    """


    @abstractmethod
    def save(
        self,
        signal: LearningSignal,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ) -> list[LearningSignal]:
        pass
