from dairyos.intelligence.decision.gateway.decision_gateway import (
    DecisionGateway,
)


class DecisionIntegration:
    """
    Integration boundary between
    intelligence prediction systems
    and decision intelligence.

    Responsibilities:

    - receive prediction outputs
    - invoke decision gateway
    - return decision intelligence results

    Future extensions:

    - event-driven integration
    - command center integration
    - external API integration
    """


    def __init__(
        self,
        gateway: DecisionGateway,
    ):

        self.gateway = gateway


    def evaluate_predictions(
        self,
        predictions: list,
    ):

        return self.gateway.evaluate(
            predictions
        )
