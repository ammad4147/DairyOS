from dairyos.intelligence.decision.services.recommendation_engine import (
    RecommendationEngine,
)

from dairyos.intelligence.decision.services.confidence_engine import (
    ConfidenceEngine,
)

from dairyos.intelligence.decision.repository.decision_repository import (
    DecisionRepository,
)


class DecisionService:
    """
    Enterprise decision intelligence service.
    """


    def __init__(
        self,
        repository: DecisionRepository,
    ):

        self.repository = repository

        self.recommendation_engine = (
            RecommendationEngine()
        )

        self.confidence_engine = (
            ConfidenceEngine()
        )


    def decide(
        self,
        predictions: list,
    ):

        recommendations = (
            self.recommendation_engine.recommend(
                predictions
            )
        )

        decisions = []


        for recommendation in recommendations:

            confidence = (
                self.confidence_engine.evaluate(
                    recommendation
                )
            )

            self.repository.save(
                recommendation
            )

            decisions.append(
                {
                    "recommendation": recommendation,
                    "confidence": confidence,
                }
            )


        return decisions


    def evaluate(
        self,
        predictions: list,
    ):

        return self.decide(
            predictions
        )


    def get_decisions(
        self,
    ):

        return self.repository.get_all()
