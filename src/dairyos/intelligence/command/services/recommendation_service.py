from dairyos.intelligence.command.models.operational_recommendation import (
    OperationalRecommendation,
)


class RecommendationService:
    """
    Generates operational recommendations.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository


    def create(
        self,
        recommendation_id: str,
        situation_id: str,
        action: str,
        urgency: str,
    ) -> OperationalRecommendation:

        recommendation = OperationalRecommendation(
            recommendation_id=recommendation_id,
            situation_id=situation_id,
            action=action,
            urgency=urgency,
        )

        return self.repository.save(
            recommendation
        )
