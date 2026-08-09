from typing import List

from ..models.learning_signal import LearningSignal


class LearningService:
    """
    Records operational learning signals.
    """

    def __init__(self):
        self.signals: List[LearningSignal] = []

    def record_signal(
        self,
        signal: LearningSignal,
    ) -> LearningSignal:

        self.signals.append(signal)

        return signal

    def get_signals(self) -> List[LearningSignal]:

        return list(self.signals)
