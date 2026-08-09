from dairyos.intelligence.decision.services import (
    RecommendationEngine,
)


class MockPrediction:

    def __init__(
        self,
        category,
        confidence,
    ):

        self.category = category

        self.confidence = confidence



def test_recommendation_engine_creates_recommendation():

    engine = RecommendationEngine()


    predictions = [
        MockPrediction(
            category="operational_risk",
            confidence=0.9,
        )
    ]


    results = engine.recommend(
        predictions
    )


    assert len(results) == 1


    recommendation = results[0]


    assert recommendation.category == (
        "operational_risk"
    )

    assert recommendation.priority == (
        "high"
    )

    assert recommendation.confidence == (
        0.9
    )



def test_recommendation_engine_ignores_unknown_prediction():

    engine = RecommendationEngine()


    predictions = [
        MockPrediction(
            category="normal_condition",
            confidence=0.9,
        )
    ]


    results = engine.recommend(
        predictions
    )


    assert len(results) == 0
