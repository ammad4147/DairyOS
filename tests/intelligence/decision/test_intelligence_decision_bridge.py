from dairyos.intelligence.decision.services.intelligence_decision_bridge import (
    IntelligenceDecisionBridge,
)

from dairyos.intelligence.models.intelligence_recommendation import (
    IntelligenceRecommendation,
)



def test_intelligence_recommendation_creates_operational_decision():

    bridge = IntelligenceDecisionBridge()


    recommendation = IntelligenceRecommendation(

        recommendation_type=
            "PRODUCTION_REVIEW",

        priority=
            "HIGH",

        source_signal=
            "MILK_PRODUCTION_VARIANCE",

        action=
            "Review feed and milking compliance",

        reasoning=
            "Milk production variance detected",

        evidence={
            "variance": -15
        },

    )


    result = (
        bridge
        .create_operational_decision(
            recommendation
        )
    )


    assert result["decision"].priority.level == "HIGH"

    assert (
        result["workflow_event"].source
        ==
        "INTELLIGENCE"
    )
