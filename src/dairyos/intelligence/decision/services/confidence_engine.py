from dairyos.intelligence.decision.models.decision_confidence import (
    DecisionConfidence,
)


class ConfidenceEngine:
    """
    Deterministic decision confidence evaluator.

    Evaluates recommendation reliability.

    Future extensions:

    - machine learning confidence models
    - historical outcome comparison
    - adaptive scoring
    """


    def evaluate(
        self,
        recommendation,
    ) -> DecisionConfidence:

        score = recommendation.confidence


        if score >= 0.8:

            level = (
                "high"
            )

        elif score >= 0.5:

            level = (
                "medium"
            )

        else:

            level = (
                "low"
            )


        return DecisionConfidence(
            recommendation_category=(
                recommendation.category
            ),
            confidence_score=(
                score
            ),
            confidence_level=(
                level
            ),
        )
