from dairyos.intelligence.models.intelligence_recommendation import (
    IntelligenceRecommendation,
)


class IntelligenceRecommendationService:
    """
    Generates decision-support recommendations.

    Recommendations guide human decisions.
    They do not execute farm actions.
    """


    def generate(
        self,
        analysis,
        signals,
    ):

        recommendations = []


        for signal in signals:

            recommendation = (
                self._recommend_for_signal(
                    signal,
                    analysis,
                )
            )


            if recommendation is not None:

                recommendations.append(
                    recommendation
                )


        return recommendations



    def _recommend_for_signal(
        self,
        signal,
        analysis,
    ):


        if signal.signal_type == (
            "MILK_PRODUCTION_VARIANCE"
        ):


            return IntelligenceRecommendation(

                recommendation_type=
                    "PRODUCTION_REVIEW",

                priority=
                    analysis.get(
                        "priority",
                        "LOW",
                    ),

                source_signal=
                    signal.signal_type,

                action=
                    "Review feed, health, and milking compliance",

                reasoning=
                    signal.message,

                evidence=
                    signal.evidence,

            )


        return IntelligenceRecommendation(

            recommendation_type=
                "OPERATIONAL_REVIEW",

            priority=
                analysis.get(
                    "priority",
                    "LOW",
                ),

            source_signal=
                signal.signal_type,

            action=
                "Review detected operational condition",

            reasoning=
                signal.message,

            evidence=
                signal.evidence,

        )
