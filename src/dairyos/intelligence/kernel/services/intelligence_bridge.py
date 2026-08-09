from typing import List

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.models.intelligence_decision import (
    IntelligenceDecision,
)

from dairyos.intelligence.kernel.services.intelligence_kernel import (
    IntelligenceKernel,
)


class IntelligenceBridge:
    """
    Connects intelligence signals with
    the core reasoning kernel.

    This service provides the transition layer
    between signal collection and decisions.
    """

    def __init__(
        self,
        kernel: IntelligenceKernel | None = None,
    ):
        self.kernel = kernel or IntelligenceKernel()

    def evaluate_signal(
        self,
        signal: IntelligenceSignal,
    ) -> IntelligenceDecision:

        return self.kernel.evaluate(signal)

    def evaluate_signals(
        self,
        signals: List[IntelligenceSignal],
    ) -> List[IntelligenceDecision]:

        decisions = []

        for signal in signals:
            decisions.append(
                self.evaluate_signal(signal)
            )

        return decisions
