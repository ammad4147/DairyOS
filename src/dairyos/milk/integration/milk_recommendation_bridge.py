from dairyos.intelligence.command.services.recommendation_service import (
    RecommendationService,
)


class MilkRecommendationBridge:
    """
    Converts milk operational situations
    into management recommendations.
    """


    def create_recommendation(
        self,
        situation,
        repository,
    ):

        service = RecommendationService(
            repository
        )


        action = (
            "Continue normal milk operations"
        )

        urgency = "LOW"


        if situation.status == "WARNING":

            action = (
                "Investigate milk production decline"
            )

            urgency = "MEDIUM"


        if situation.status == "CRITICAL":

            action = (
                "Immediate investigation required "
                "for milk production decline"
            )

            urgency = "HIGH"


        return service.create(

            recommendation_id=(
                "MILK-REC-"
                +
                situation.situation_id
            ),

            situation_id=situation.situation_id,

            action=action,

            urgency=urgency,

        )
