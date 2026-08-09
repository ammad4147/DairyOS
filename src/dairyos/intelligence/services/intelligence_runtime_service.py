from dairyos.intelligence.context.intelligence_context_builder import (
    IntelligenceContextBuilder,
)

from dairyos.intelligence.services.intelligence_orchestrator import (
    IntelligenceOrchestrator,
)



class IntelligenceRuntimeService:
    """
    Runtime entry point for DairyOS intelligence evaluation.

    Responsibilities:
    - Reads FarmOperationalState.
    - Builds intelligence context.
    - Executes intelligence pipeline.

    Does not:
    - mutate operational state.
    - create operational events.
    - execute recommendations.
    """



    def __init__(
        self,
        context_builder=None,
        orchestrator=None,
    ):

        self.context_builder = (
            context_builder
            if context_builder is not None
            else IntelligenceContextBuilder()
        )


        self.orchestrator = (
            orchestrator
            if orchestrator is not None
            else IntelligenceOrchestrator()
        )



    def evaluate_state(
        self,
        state,
    ):

        context = (
            self.context_builder
            .build(state)
        )


        return (
            self.orchestrator
            .evaluate(context)
        )
