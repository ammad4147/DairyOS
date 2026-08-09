from dairyos.intelligence.prediction.services.prediction_service import (
    PredictionService,
)


class PredictionGateway:
    """
    Gateway boundary for prediction intelligence.
    """

    def __init__(self, service=None):

        if service is None:
            from dairyos.intelligence.prediction.repository.adapters.memory_prediction_repository import (
                MemoryPredictionRepository,
            )

            service = PredictionService(
                MemoryPredictionRepository()
            )

        self.service = service


    def predict(self, signals):

        return self.service.predict(
            signals
        )


    def get_predictions(self, context=None):

        if hasattr(self.service, "get_predictions"):

            if context is None:
                return self.service.get_predictions()

            return self.service.get_predictions(
                context
            )

        return []
