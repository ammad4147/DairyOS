from dairyos.intelligence.decision.services import (
    ConfidenceEngine,
)

from dairyos.intelligence.decision.models import (
    DecisionRecommendation,
)


def test_high_confidence_classification():

    engine = ConfidenceEngine()


    recommendation = DecisionRecommendation(
        category="operational_risk",
        recommendation="Review conditions",
        rationale="Risk detected",
        confidence=0.9,
        priority="high",
    )


    result = engine.evaluate(
        recommendation
    )


    assert result.confidence_score == 0.9

    assert result.confidence_level == (
        "high"
    )



def test_medium_confidence_classification():

    engine = ConfidenceEngine()


    recommendation = DecisionRecommendation(
        category="operational_risk",
        recommendation="Monitor conditions",
        rationale="Moderate risk",
        confidence=0.6,
        priority="medium",
    )


    result = engine.evaluate(
        recommendation
    )


    assert result.confidence_level == (
        "medium"
    )



def test_low_confidence_classification():

    engine = ConfidenceEngine()


    recommendation = DecisionRecommendation(
        category="operational_risk",
        recommendation="Observe",
        rationale="Low certainty",
        confidence=0.3,
        priority="low",
    )


    result = engine.evaluate(
        recommendation
    )


    assert result.confidence_level == (
        "low"
    )
