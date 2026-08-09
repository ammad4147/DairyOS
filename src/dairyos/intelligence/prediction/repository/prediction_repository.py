from abc import ABC, abstractmethod

from dairyos.intelligence.prediction.models.prediction_result import (
    PredictionResult,
)


class PredictionRepository(ABC):
    """
    Enterprise persistence contract
    for intelligence predictions.

    Implementations may include:

    - memory repository
    - PostgreSQL adapter
    - event storage adapter
    """


    @abstractmethod
    def save(
        self,
        prediction: PredictionResult,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ) -> list[PredictionResult]:
        pass
