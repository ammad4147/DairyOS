from dairyos.intelligence.kernel.context.intelligence_context import (
    IntelligenceContext,
)

from dairyos.intelligence.kernel.assessment.situation_assessment import (
    SituationAssessment,
)

from dairyos.intelligence.kernel.prioritization.decision_prioritizer import (
    DecisionPrioritizer,
)

from dairyos.intelligence.kernel.recommendation.recommendation_engine import (
    RecommendationEngine,
)

from dairyos.intelligence.kernel.synthesis.decision_synthesizer import (
    DecisionSynthesizer,
)


class IntelligenceOrchestrator:
    """
    Coordinates the complete DairyOS intelligence reasoning pipeline.

    Flow:

    Intelligence Context
            |
            v
    Situation Assessment
            |
            v
    Decision Prioritization
            |
            v
    Recommendation Generation
            |
            v
    Decision Synthesis
    """


    def __init__(self):

        self.assessment = SituationAssessment()
        self.prioritizer = DecisionPrioritizer()
        self.recommendation_engine = RecommendationEngine()
        self.synthesizer = DecisionSynthesizer()


    def process(
        self,
        context: IntelligenceContext,
    ) -> dict:

        assessment = self.assessment.assess(
            context
        )

        priorities = self.prioritizer.prioritize(
            context
        )

        recommendations = self.recommendation_engine.generate(
            priorities
        )

        decisions = self.synthesizer.synthesize(
            recommendations
        )

        return {
            "assessment": assessment,
            "priorities": priorities,
            "recommendations": recommendations,
            "decisions": decisions,
        }
