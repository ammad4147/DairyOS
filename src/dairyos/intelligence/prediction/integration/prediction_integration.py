from dairyos.intelligence.prediction.gateway.prediction_gateway import (
    PredictionGateway,
)


class PredictionIntegration:
    """
    Integration boundary for predictive intelligence.

    Converts learned intelligence signals
    into future operational predictions.
    """


    def __init__(
        self,
        gateway: PredictionGateway,
    ):

        self.gateway = gateway


    def generate_predictions(
        self,
        signals: list,
    ):

        return self.gateway.predict(
            signals
        )


    def get_predictions(
        self,
    ):

        return self.gateway.get_predictions()
