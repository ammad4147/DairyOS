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


def test_complete_intelligence_prediction_flow():

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


    learned_signals = [

        LearningSignal(
            category="operational_risk",
            description=(
                "Repeated critical herd events"
            ),
            confidence=0.9,
        )

    ]


    predictions = integration.generate_predictions(
        learned_signals
    )


    assert len(predictions) == 1


    prediction = predictions[0]


    assert prediction.category == (
        "operational_risk"
    )


    assert prediction.confidence == 0.9


    assert prediction.horizon == (
        "near_term"
    )


    stored = integration.get_predictions()


    assert len(stored) == 1
