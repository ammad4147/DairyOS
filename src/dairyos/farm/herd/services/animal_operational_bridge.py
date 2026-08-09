from dairyos.farm.herd.services.animal_event_projection import (
    AnimalEventProjection,
)

from dairyos.farm.herd.services.animal_intelligence_service import (
    AnimalIntelligenceService,
)

from dairyos.farm.herd.services.animal_recommendation_service import (
    AnimalRecommendationService,
)

from dairyos.operations.decisions.services.farm_operational_decision_bridge import (
    FarmOperationalDecisionBridge,
)


class AnimalOperationalBridge:
    """
    Connects animal operational events,
    intelligence evaluation,
    recommendations,
    and operational decisions.

    Single recommendation path:

        Farm Event
            |
            v
        Animal State Projection
            |
            v
        Animal Intelligence
            |
            v
        Animal Recommendation Service
            |
            v
        Operational Decision Bridge


    Intelligence observes.
    Recommendations translate.
    Decisions govern.
    """


    def __init__(
        self,
        projection=None,
        intelligence_service=None,
        recommendation_service=None,
        decision_bridge=None,
    ):

        self.projection = (
            projection
            if projection is not None
            else AnimalEventProjection()
        )

        self.intelligence_service = (
            intelligence_service
            if intelligence_service is not None
            else AnimalIntelligenceService()
        )

        self.recommendation_service = (
            recommendation_service
            if recommendation_service is not None
            else AnimalRecommendationService()
        )

        self.decision_bridge = (
            decision_bridge
            if decision_bridge is not None
            else FarmOperationalDecisionBridge()
        )


    def process(
        self,
        event,
    ):

        state = self.projection.apply(event)

        if state is None:
            return None

        return self.intelligence_service.evaluate(
            state
        )


    def process_with_decisions(
        self,
        event,
    ):

        state = self.process(event)

        if state is None:

            return {
                "state": None,
                "decisions": [],
            }


        decisions = (
            self.create_decisions_from_state(
                state
            )
        )


        return {
            "state": state,
            "decisions": decisions,
        }


    def create_decisions_from_state(
        self,
        state,
    ):

        recommendations = []


        intelligence_recommendations = (
            self.recommendation_service.generate(
                state
            )
        )


        for recommendation in intelligence_recommendations:

            recommendations.append(

                {
                    "source":
                        f"animal:{state.animal_id}",

                    "type":
                        recommendation.recommendation_type,

                    "title":
                        recommendation.action,

                    "details":
                        recommendation.reasoning,

                    "priority":
                        recommendation.priority,

                }

            )


        return (
            self.decision_bridge
            .create_from_recommendations(
                recommendations
            )
        )


    def get_animal_state(
        self,
        animal_id: str,
    ):

        return self.projection.get_state(
            animal_id
        )


    def get_all_states(
        self,
    ):

        return self.projection.all_states()
