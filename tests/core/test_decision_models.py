from dairyos.intelligence.decision.models import (
    DecisionRecommendation,
    DecisionConfidence,
)


def test_decision_recommendation_creation():

    recommendation = DecisionRecommendation(
        category="operational_risk",
        recommendation="Review conditions",
        rationale="Risk detected",
        confidence=0.8,
        priority="high",
    )


    assert recommendation.category == (
        "operational_risk"
    )

    assert recommendation.confidence == (
        0.8
    )


def test_decision_confidence_creation():

    confidence = DecisionConfidence(
        recommendation_category=(
            "operational_risk"
        ),
        confidence_score=0.8,
        confidence_level="high",
    )


    assert confidence.confidence_score == (
        0.8
    )

    assert confidence.confidence_level == (
        "high"
    )
