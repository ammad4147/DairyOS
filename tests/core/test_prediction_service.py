from dairyos.intelligence.prediction.services.prediction_service import (
    PredictionService,
)

from dairyos.intelligence.prediction.repository.adapters.memory_prediction_repository import (
    MemoryPredictionRepository,
)

from dairyos.intelligence.learning.models.learning_signal import (
    LearningSignal,
)


def test_prediction_service_creates_prediction():

    repository = MemoryPredictionRepository()


    service = PredictionService(
        repository
    )


    signals = [
        LearningSignal(
            category="operational_risk",
            description=(
                "Repeated critical events"
            ),
            confidence=0.8,
        )
    ]


    predictions = service.predict(
        signals
    )


    assert len(predictions) == 1


    stored = service.get_predictions()


    assert len(stored) == 1


    assert stored[0].category == (
        "operational_risk"
    )
