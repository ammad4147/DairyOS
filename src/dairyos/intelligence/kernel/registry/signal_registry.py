from dairyos.intelligence.kernel.models.intelligence_signal import IntelligenceSignal


class IntelligenceSignalRegistry:
    """
    Central registry for intelligence signals.

    Provides a common intake point for
    all DairyOS intelligence domains.
    """

    def __init__(self):
        self._signals = []


    def register(
        self,
        signal: IntelligenceSignal,
    ) -> IntelligenceSignal:

        self._signals.append(signal)

        return signal


    def get_all(self):

        return list(self._signals)


    def count(self) -> int:

        return len(self._signals)



SignalRegistry = IntelligenceSignalRegistry

