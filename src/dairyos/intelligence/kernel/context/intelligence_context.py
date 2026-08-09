from dairyos.intelligence.kernel.models.intelligence_signal import IntelligenceSignal
from dairyos.intelligence.kernel.models.intelligence_decision import IntelligenceDecision
from dairyos.intelligence.kernel.models.intelligence_outcome import IntelligenceOutcome


class IntelligenceContext:
    """
    Current operational intelligence context.

    Maintains a combined view of:
    - observed signals
    - generated decisions
    - completed outcomes

    Foundation for future:
    - situational awareness
    - intelligence learning
    - predictive reasoning
    """

    def __init__(self):

        self.signals = []
        self.decisions = []
        self.outcomes = []


    def add_signal(
        self,
        signal: IntelligenceSignal,
    ):

        self.signals.append(signal)

        return signal


    def add_decision(
        self,
        decision: IntelligenceDecision,
    ):

        self.decisions.append(decision)

        return decision


    def add_outcome(
        self,
        outcome: IntelligenceOutcome,
    ):

        self.outcomes.append(outcome)

        return outcome


    def summary(self):

        return {
            "signals": len(self.signals),
            "decisions": len(self.decisions),
            "outcomes": len(self.outcomes),
        }
