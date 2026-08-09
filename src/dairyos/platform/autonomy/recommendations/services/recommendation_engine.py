from dairyos.platform.autonomy.recommendations.models.recommendation import (
    Recommendation,
)



class RecommendationEngine:
    """
    Converts decision context into recommended actions.
    """



    def generate(

        self,

        context,

    ):


        return Recommendation(

            title=context.problem,

            action="Review operational condition",

            reason=", ".join(context.evidence),

            expected_outcome=context.impact,

            confidence=context.confidence,

            priority="high",

        )

