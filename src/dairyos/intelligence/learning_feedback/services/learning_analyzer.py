from dairyos.intelligence.learning_feedback.models.learning_event import (
    LearningEvent,
)


class LearningAnalyzer:
    """
    Analyses operational outcomes.

    Future extensions:

    - pattern detection
    - anomaly discovery
    - predictive improvement
    """


    def analyze(
        self,
        feedback,
    ) -> LearningEvent:

        description = (
            "Successful execution pattern detected"
            if feedback.success
            else
            "Execution failure pattern detected"
        )

        return LearningEvent(
            event_type="execution_analysis",
            source=feedback.workflow_type,
            description=description,
        )
