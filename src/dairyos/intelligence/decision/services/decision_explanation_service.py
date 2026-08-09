"""
DairyOS Decision Explainability Service

Creates deterministic explanations
for autonomous intelligence decisions.
"""


class DecisionExplanationService:
    """
    Builds human-readable decision explanations.
    """



    def explain(
        self,
        decision_result,
    ):

        explanation = {
            "category": None,
            "recommendation": None,
            "rationale": None,
            "confidence": None,
            "confidence_level": None,
            "priority": None,
        }


        if not decision_result:

            return explanation



        if isinstance(
            decision_result,
            list,
        ):

            decision_result = decision_result[0]



        if isinstance(
            decision_result,
            dict,
        ):

            recommendation = (
                decision_result.get(
                    "recommendation"
                )
            )

            confidence = (
                decision_result.get(
                    "confidence"
                )
            )


            if recommendation:

                explanation["category"] = (
                    recommendation.category
                )

                explanation["recommendation"] = (
                    recommendation.recommendation
                )

                explanation["rationale"] = (
                    recommendation.rationale
                )

                explanation["priority"] = (
                    recommendation.priority
                )


            if confidence:

                explanation["confidence"] = (
                    confidence.confidence_score
                )

                explanation["confidence_level"] = (
                    confidence.confidence_level
                )



        return explanation
