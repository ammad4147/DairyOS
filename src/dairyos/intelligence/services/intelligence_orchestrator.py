from dairyos.intelligence.registry.signal_registry import (
    IntelligenceSignalRegistry,
)

from dairyos.intelligence.services.intelligence_detection_service import (
    IntelligenceDetectionService,
)

from dairyos.intelligence.services.intelligence_analysis_service import (
    IntelligenceAnalysisService,
)

from dairyos.intelligence.services.intelligence_recommendation_service import (
    IntelligenceRecommendationService,
)

from dairyos.intelligence.models.intelligence_pipeline_result import (
    IntelligencePipelineResult,
)



class IntelligenceOrchestrator:
    """
    Coordinates the DairyOS intelligence pipeline.

    Flow:

    Operational Context
            |
            v
    Signal Registry
            |
            v
    Analysis
            |
            v
    Recommendation


    Intelligence observes and advises.
    It never changes operational facts.
    """



    def __init__(
        self,
        detection_service=None,
        analysis_service=None,
        recommendation_service=None,
        signal_registry=None,
    ):

        self.detection_service = (
            detection_service
            if detection_service is not None
            else IntelligenceDetectionService()
        )


        self.signal_registry = (
            signal_registry
            if signal_registry is not None
            else IntelligenceSignalRegistry()
        )


        self.analysis_service = (
            analysis_service
            if analysis_service is not None
            else IntelligenceAnalysisService()
        )


        self.recommendation_service = (
            recommendation_service
            if recommendation_service is not None
            else IntelligenceRecommendationService()
        )



    def evaluate(
        self,
        operational_context,
    ):

        signals = (
            self.signal_registry.detect(
                operational_context
            )
        )


        analysis = (
            self.analysis_service.analyze(
                signals
            )
        )


        recommendations = (
            self.recommendation_service.generate(
                analysis,
                signals,
            )
        )


        return IntelligencePipelineResult(

            signals=signals,

            analysis=analysis,

            recommendations=recommendations,

            execution_metadata={

                "pipeline":
                    "intelligence",

                "status":
                    "completed",

            },

        )
