from dairyos.intelligence.prediction.services.prediction_analyzer import (
    PredictionAnalyzer,
)

from dairyos.intelligence.prediction.repository.prediction_repository import (
    PredictionRepository,
)


class PredictionService:
    """
    Enterprise prediction service.

    Responsibilities:

    - analyze learning signals
    - create predictions
    - persist predictions
    """


    def __init__(
        self,
        repository: PredictionRepository,
    ):

        self.repository = repository

        self.analyzer = PredictionAnalyzer()


    def predict(
        self,
        signals: list,
    ):

        predictions = self.analyzer.predict(
            signals
        )


        for prediction in predictions:

            self.repository.save(
                prediction
            )


        return predictions


    def get_predictions(
        self,
    ):

        return self.repository.get_all()
