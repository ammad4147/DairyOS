from abc import ABC, abstractmethod


class SignalDetector(ABC):
    """
    Base contract for intelligence detectors.

    Detectors observe context and return signals.
    They never modify operational state.
    """


    @abstractmethod
    def detect(
        self,
        operational_context,
    ):

        raise NotImplementedError
