class WorkflowIntelligenceDecisionGateway:
    """
    Integration boundary for operational workflow decisions.

    Exposes rule-based operational decisions
    without exposing intelligence internals.
    """


    def __init__(
        self,
        decision_service,
    ):

        self.decision_service = decision_service



    def get_operational_decisions(
        self,
    ):

        return (
            self.decision_service
            .generate_decisions()
        )
