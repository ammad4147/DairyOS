from dairyos.intelligence.kernel.context.intelligence_context import (
    IntelligenceContext,
)

from dairyos.intelligence.kernel.orchestration.intelligence_orchestrator import (
    IntelligenceOrchestrator,
)


class IntelligenceGateway:
    """
    External entry boundary for the DairyOS intelligence kernel.

    Responsibilities:

    - receive intelligence context
    - invoke intelligence orchestration
    - return structured intelligence result

    This boundary allows future integration with:

    - API layer
    - automation layer
    - agent systems
    - external decision interfaces
    """


    def __init__(self):

        self.orchestrator = IntelligenceOrchestrator()


    def process(
        self,
        context: IntelligenceContext,
    ) -> dict:

        return self.orchestrator.process(
            context
        )
