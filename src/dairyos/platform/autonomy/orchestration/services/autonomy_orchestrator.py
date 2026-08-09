from dairyos.platform.autonomy.context.services.context_engine import (
    ContextEngine,
)

from dairyos.platform.autonomy.recommendations.services.recommendation_engine import (
    RecommendationEngine,
)



class AutonomyOrchestrator:
    """
    Coordinates autonomous decision workflow.
    """



    def __init__(self):

        self.context_engine = ContextEngine()

        self.recommendation_engine = RecommendationEngine()



    def analyze(

        self,

        problem,

        evidence,

        impact,

        confidence,

    ):


        context = self.context_engine.build(

            problem,

            evidence,

            impact,

            confidence,

        )


        recommendation = self.recommendation_engine.generate(

            context

        )


        return {

            "context": context,

            "recommendation": recommendation,

        }

