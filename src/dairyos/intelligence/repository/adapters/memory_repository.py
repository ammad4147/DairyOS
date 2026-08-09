from dairyos.intelligence.repository.intelligence_repository import (
    IntelligenceRepository,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.models.intelligence_decision import (
    IntelligenceDecision,
)

from dairyos.intelligence.kernel.models.intelligence_outcome import (
    IntelligenceOutcome,
)


class InMemoryIntelligenceRepository(
    IntelligenceRepository
):
    """
    In-memory implementation of the intelligence repository contract.

    Used for:

    - development
    - testing
    - validation

    Future adapters may replace this implementation
    without changing service-layer code.
    """


    def __init__(self):

        self._signals = []
        self._decisions = []
        self._outcomes = []


    def save_signal(
        self,
        signal: IntelligenceSignal,
    ):

        self._signals.append(
            signal
        )

        return signal


    def save_decision(
        self,
        decision: IntelligenceDecision,
    ):

        self._decisions.append(
            decision
        )

        return decision


    def save_outcome(
        self,
        outcome: IntelligenceOutcome,
    ):

        self._outcomes.append(
            outcome
        )

        return outcome


    def get_signals(
        self,
    ) -> list[IntelligenceSignal]:

        return list(
            self._signals
        )


    def get_decisions(
        self,
    ) -> list[IntelligenceDecision]:

        return list(
            self._decisions
        )


    def get_outcomes(
        self,
    ) -> list[IntelligenceOutcome]:

        return list(
            self._outcomes
        )
