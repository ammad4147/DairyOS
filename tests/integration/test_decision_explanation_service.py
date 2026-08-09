from dairyos.intelligence.decision.services.decision_explanation_service import (
    DecisionExplanationService,
)

from dairyos.intelligence.decision.models.decision_recommendation import (
    DecisionRecommendation,
)

from dairyos.intelligence.decision.models.decision_confidence import (
    DecisionConfidence,
)


def test_decision_explanation_generation():

    service = DecisionExplanationService()


    result = service.explain(
        {
            "recommendation": DecisionRecommendation(
                category="operational_risk",
                recommendation="Review operational conditions",
                rationale="Prediction indicates potential future risk",
                confidence=0.85,
                priority="high",
            ),
            "confidence": DecisionConfidence(
                recommendation_category="operational_risk",
                confidence_score=0.85,
                confidence_level="high",
            ),
        }
    )


    assert result["category"] == (
        "operational_risk"
    )

    assert result["confidence_level"] == (
        "high"
    )

    assert result["priority"] == (
        "high"
    )
