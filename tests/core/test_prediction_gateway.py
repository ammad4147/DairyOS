from dairyos.intelligence.prediction.gateway.prediction_gateway import (
    PredictionGateway,
)

from dairyos.intelligence.prediction.services.prediction_service import (
    PredictionService,
)

from dairyos.intelligence.prediction.repository.adapters.memory_prediction_repository import (
    MemoryPredictionRepository,
)

from dairyos.intelligence.learning.models.learning_signal import (
    LearningSignal,
)


def test_prediction_gateway_executes_prediction_flow():

    repository = MemoryPredictionRepository()


    service = PredictionService(
        repository
    )


    gateway = PredictionGateway(
        service
    )


    signals = [
        LearningSignal(
            category="operational_risk",
            description=(
                "Critical pattern detected"
            ),
            confidence=0.9,
        )
    ]


    predictions = gateway.predict(
        signals
    )


    assert len(predictions) == 1


    stored = gateway.get_predictions()


    assert len(stored) == 1


    assert stored[0].horizon == (
        "near_term"
    )
