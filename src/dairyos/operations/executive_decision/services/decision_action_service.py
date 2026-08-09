from ..models.decision_urgency import DecisionUrgency


class DecisionActionService:
    """
    Determines whether management action is required.
    """


    def requires_action(
        self,
        decision,
    ):

        return decision.urgency in [
            DecisionUrgency.URGENT,
            DecisionUrgency.CRITICAL,
        ]
