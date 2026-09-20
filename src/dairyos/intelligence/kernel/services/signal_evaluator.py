from dataclasses import dataclass

from dairyos.intelligence.kernel.models.intelligence_outcome import (
    IntelligenceOutcome,
)
from dairyos.intelligence.kernel.registry.signal_registry import (
    IntelligenceSignalRegistry,
)


@dataclass
class IntelligenceEvaluation:
    signal_name: str
    priority: str
    status: str
    message: str


class SignalEvaluator:
    """
    Core intelligence kernel evaluation service.

    Converts registered intelligence signals
    into evaluated intelligence outcomes.
    """

    def __init__(
        self,
        registry: IntelligenceSignalRegistry,
    ):
        self.registry = registry


    def evaluate(self) -> list[IntelligenceEvaluation]:

        evaluations = []

        for signal in self.registry.get_all():

            evaluations.append(
                IntelligenceEvaluation(
                    signal_name=signal.category,
                    priority=signal.severity,
                    status="evaluated",
                    message=signal.message,
                )
            )

        return evaluations


    def evaluate_outcomes(self) -> list[IntelligenceOutcome]:

        outcomes = []

        for evaluation in self.evaluate():

            outcomes.append(
                IntelligenceOutcome.create(
                    signal_name=evaluation.signal_name,
                    priority=evaluation.priority,
                    recommendation=evaluation.message,
                )
            )

        return outcomes
