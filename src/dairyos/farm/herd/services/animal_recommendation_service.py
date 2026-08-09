from dairyos.farm.herd.models.animal_operational_state import (
    AnimalOperationalState,
)

from dairyos.intelligence.models.intelligence_recommendation import (
    IntelligenceRecommendation,
)


class AnimalRecommendationService:
    """
    Converts animal intelligence attention
    into operational recommendations.

    This is the single translation layer.

    It does not:
    - mutate animal state
    - create commands
    - execute actions
    """


    def generate(
        self,
        state: AnimalOperationalState,
    ) -> list[IntelligenceRecommendation]:

        recommendations = []


        attention_items = []


        #
        # Intelligence attention is the primary source.
        #
        if hasattr(
            state,
            "intelligence_attention_reason",
        ):

            attention_items.extend(
                state.intelligence_attention_reason
            )


        #
        # Compatibility with operational attention.
        # No second recommendation path exists.
        #
        if not attention_items and hasattr(
            state,
            "attention_items",
        ):

            attention_items.extend(
                state.attention_items
            )


        for attention in attention_items:

            recommendation = (
                self._from_attention(
                    state,
                    attention,
                )
            )


            if recommendation is not None:

                recommendations.append(
                    recommendation
                )


        return recommendations



    def _from_attention(
        self,
        state,
        attention: str,
    ):

        if (
            "Milk production"
            in attention
        ):

            return IntelligenceRecommendation(

                recommendation_type=
                    "ANIMAL_PRODUCTION_REVIEW",

                priority=
                    "HIGH",

                source_signal=
                    "ANIMAL_MILK_DEVIATION",

                action=
                    "Review feed, health and milking compliance",

                reasoning=
                    attention,

                evidence={
                    "animal_id":
                        state.animal_id,
                },

            )


        if (
            "Health"
            in attention
        ):

            return IntelligenceRecommendation(

                recommendation_type=
                    "ANIMAL_HEALTH_REVIEW",

                priority=
                    "HIGH",

                source_signal=
                    "ANIMAL_HEALTH_ALERT",

                action=
                    "Perform animal health review",

                reasoning=
                    attention,

                evidence={
                    "animal_id":
                        state.animal_id,
                },

            )


        return IntelligenceRecommendation(

            recommendation_type=
                "ANIMAL_OPERATIONAL_REVIEW",

            priority=
                "LOW",

            source_signal=
                "ANIMAL_OPERATIONAL_ALERT",

            action=
                "Review animal operational condition",

            reasoning=
                attention,

            evidence={
                "animal_id":
                    state.animal_id,
            },

        )
