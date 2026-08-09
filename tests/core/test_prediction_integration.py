from dairyos.intelligence.prediction.integration.prediction_integration import (
    PredictionIntegration,
)

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


def test_prediction_integration_generates_predictions():

    repository = MemoryPredictionRepository()


    service = PredictionService(
        repository
    )


    gateway = PredictionGateway(
        service
    )


    integration = PredictionIntegration(
        gateway
    )


    signals = [
        LearningSignal(
            category="operational_risk",
            description=(
                "Critical event pattern"
            ),
            confidence=0.85,
        )
    ]


    predictions = integration.generate_predictions(
        signals
    )


    assert len(predictions) == 1


    stored = integration.get_predictions()


    assert len(stored) == 1


    assert stored[0].prediction == (
        "Future operational risk likely"
    )
