from dairyos.intelligence.decision.integration import (
    DecisionIntegration,
)

from dairyos.intelligence.decision.gateway import (
    DecisionGateway,
)

from dairyos.intelligence.decision.services import (
    DecisionService,
)

from dairyos.intelligence.decision.repository.adapters import (
    MemoryDecisionRepository,
)



class MockPrediction:

    def __init__(
        self,
        category,
        confidence,
    ):

        self.category = category

        self.confidence = confidence



def test_decision_integration_flow():

    repository = MemoryDecisionRepository()


    service = DecisionService(
        repository
    )


    gateway = DecisionGateway(
        service
    )


    integration = DecisionIntegration(
        gateway
    )


    predictions = [
        MockPrediction(
            category="operational_risk",
            confidence=0.85,
        )
    ]


    results = integration.evaluate_predictions(
        predictions
    )


    assert len(results) == 1


    assert (
        results[0]["confidence"]
        .confidence_level
        ==
        "high"
    )


    assert len(
        repository.get_all()
    ) == 1
