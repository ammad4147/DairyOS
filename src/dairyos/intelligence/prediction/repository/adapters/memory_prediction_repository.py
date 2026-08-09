from dairyos.intelligence.prediction.models.prediction_result import (
    PredictionResult,
)


class MemoryPredictionRepository:
    """
    In-memory prediction repository.

    Used for:

    - testing
    - development
    - future adapter validation
    """


    def __init__(
        self,
    ):

        self.predictions = []


    def save(
        self,
        prediction: PredictionResult,
    ):

        self.predictions.append(
            prediction
        )


    def get_all(
        self,
    ) -> list[PredictionResult]:

        return self.predictions
