from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)
from dairyos.intelligence.kernel.models.intelligence_decision import (
    IntelligenceDecision,
)
from dairyos.intelligence.kernel.services.intelligence_kernel import (
    IntelligenceKernel,
)


class IntelligenceDomainIntegration:
    """
    Integration layer between DairyOS intelligence domains
    and the intelligence kernel.

    Responsible for:
    - accepting domain intelligence signals
    - forwarding signals to kernel reasoning
    - returning structured decisions
    """

    def __init__(self):

        self.kernel = IntelligenceKernel()


    def process_signal(
        self,
        signal: IntelligenceSignal,
    ) -> IntelligenceDecision:

        return self.kernel.evaluate(signal)