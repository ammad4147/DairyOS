from dairyos.intelligence.kernel.models.intelligence_signal import IntelligenceSignal
from dairyos.intelligence.kernel.models.intelligence_decision import IntelligenceDecision
from dairyos.intelligence.kernel.models.intelligence_outcome import IntelligenceOutcome


class IntelligenceMemory:
    """
    In-memory history store for DairyOS intelligence kernel.

    Maintains traceability between:
    - signals received
    - decisions generated
    - outcomes recorded

    Future versions may replace this storage
    with persistent enterprise memory.
    """

    def __init__(self):
        self._signals = []
        self._decisions = []
        self._outcomes = []

    def store_signal(
        self,
        signal: IntelligenceSignal,
    ) -> IntelligenceSignal:

        self._signals.append(signal)

        return signal


    def store_decision(
        self,
        decision: IntelligenceDecision,
    ) -> IntelligenceDecision:

        self._decisions.append(decision)

        return decision


    def store_outcome(
        self,
        outcome: IntelligenceOutcome,
    ) -> IntelligenceOutcome:

        self._outcomes.append(outcome)

        return outcome


    def get_signals(self):

        return list(self._signals)


    def get_decisions(self):

        return list(self._decisions)


    def get_outcomes(self):

        return list(self._outcomes)


    def signal_count(self) -> int:

        return len(self._signals)


    def decision_count(self) -> int:

        return len(self._decisions)


    def outcome_count(self) -> int:

        return len(self._outcomes)
