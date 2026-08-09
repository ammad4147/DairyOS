from dairyos.intelligence.kernel.models.intelligence_signal import IntelligenceSignal
from dairyos.intelligence.kernel.models.intelligence_decision import IntelligenceDecision


class IntelligenceKernel:
    """
    Core reasoning coordinator for DairyOS intelligence domains.

    Initial foundation:
    - receives intelligence signals
    - evaluates basic decision flow
    - produces structured decisions

    Future extensions:
    - learning memory
    - predictive reasoning
    - autonomous agents
    """


    def evaluate(
        self,
        signal: IntelligenceSignal,
    ) -> IntelligenceDecision:

        if signal.severity == "critical":
            return IntelligenceDecision(
                action="Immediate attention required",
                rationale=signal.message,
                priority="high",
            )

        return IntelligenceDecision(
            action="Monitor situation",
            rationale=signal.message,
            priority="normal",
        )

