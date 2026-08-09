from dairyos.intelligence.decision.models.decision_recommendation import (
    DecisionRecommendation,
)


class RecommendationEngine:
    """
    Deterministic decision recommendation engine.

    Converts predictions into
    actionable intelligence recommendations.

    Future extensions:

    - ranking models
    - optimization algorithms
    - reinforcement learning
    """


    def recommend(
        self,
        predictions: list,
    ) -> list[DecisionRecommendation]:

        recommendations = []


        for prediction in predictions:

            if prediction.category == (
                "operational_risk"
            ):

                recommendations.append(
                    DecisionRecommendation(
                        category=(
                            "operational_risk"
                        ),
                        recommendation=(
                            "Review operational "
                            "conditions"
                        ),
                        rationale=(
                            "Prediction indicates "
                            "potential future risk"
                        ),
                        confidence=(
                            prediction.confidence
                        ),
                        priority=(
                            "high"
                        ),
                    )
                )


        return recommendations
