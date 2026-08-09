from dairyos.intelligence.read_models.intelligence_summary import (
    IntelligenceSummary,
)


class IntelligenceQueryService:
    """
    Read boundary for intelligence.

    Converts intelligence runtime output
    into dashboard-safe intelligence summaries.

    Rules:
    - Read only.
    - No operational state mutation.
    - No recommendation execution.
    """


    def __init__(
        self,
        intelligence_runtime_service,
    ):

        self.intelligence_runtime_service = (
            intelligence_runtime_service
        )



    def get_current_intelligence(
        self,
        state=None,
    ):

        result = (
            self.intelligence_runtime_service
            .evaluate_state(
                state
            )
        )


        return (
            IntelligenceSummary
            .from_pipeline_result(
                result
            )
        )
