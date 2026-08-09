from dairyos.intelligence.kernel.models.intelligence_outcome import (
    IntelligenceOutcome,
)

from dairyos.intelligence.kernel.models.intelligence_decision import (
    IntelligenceDecision,
)


class OutcomeTracker:
    """
    Tracks intelligence kernel outcomes.

    Foundation capability:
    - converts decisions into structured outcomes
    - keeps outcome history
    - prepares future learning feedback
    """


    def __init__(self):

        self._outcomes = []


    def record(
        self,
        decision: IntelligenceDecision,
    ) -> IntelligenceOutcome:

        outcome = IntelligenceOutcome.create(
            signal_name=decision.rationale,
            priority=decision.priority,
            recommendation=decision.action,
        )

        self._outcomes.append(outcome)

        return outcome


    def get_all(self):

        return list(self._outcomes)


    def count(self) -> int:

        return len(self._outcomes)
