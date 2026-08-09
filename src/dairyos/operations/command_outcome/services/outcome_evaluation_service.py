from ..models.outcome_status import OutcomeStatus


class OutcomeEvaluationService:
    """
    Evaluates operational effectiveness.
    """


    def requires_improvement(
        self,
        outcome,
    ):

        return outcome.status in [
            OutcomeStatus.PARTIAL,
            OutcomeStatus.UNSUCCESSFUL,
        ]
