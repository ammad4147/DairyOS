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



def test_decision_service_orchestration():

    repository = MemoryDecisionRepository()


    service = DecisionService(
        repository
    )


    predictions = [
        MockPrediction(
            category="operational_risk",
            confidence=0.9,
        )
    ]


    results = service.decide(
        predictions
    )


    assert len(results) == 1


    decision = results[0]


    assert (
        decision["confidence"]
        .confidence_level
        ==
        "high"
    )


    stored = repository.get_all()


    assert len(stored) == 1



def test_decision_service_no_recommendations():

    repository = MemoryDecisionRepository()


    service = DecisionService(
        repository
    )


    predictions = [
        MockPrediction(
            category="normal_condition",
            confidence=0.9,
        )
    ]


    results = service.decide(
        predictions
    )


    assert results == []

    assert repository.get_all() == []
