from dairyos.intelligence.learning_feedback.models.learning_score import (
    LearningScore,
)


class LearningScorer:
    """
    Calculates intelligence effectiveness.

    Future extensions:

    - adaptive scoring
    - model benchmarking
    """


    def score(
        self,
        decision_type: str,
        accuracy_score: float,
        execution_score: float,
        confidence_score: float,
    ) -> LearningScore:

        return LearningScore(
            decision_type=decision_type,
            accuracy_score=accuracy_score,
            execution_score=execution_score,
            confidence_score=confidence_score,
        )
