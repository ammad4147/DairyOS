from dairyos.intelligence.learning_feedback.models.learning_feedback import (
    LearningFeedback,
)


class LearningFeedbackService:
    """
    Captures execution feedback.

    Responsibilities:

    - create feedback records
    - store execution learning
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository


    def capture(
        self,
        decision_type: str,
        workflow_type: str,
        execution_result: str,
        success: bool,
        feedback: str,
    ) -> LearningFeedback:

        item = LearningFeedback(
            decision_type=decision_type,
            workflow_type=workflow_type,
            execution_result=execution_result,
            success=success,
            feedback=feedback,
        )

        self.repository.save(
            item
        )

        return item


    def get_feedback(
        self,
    ):

        return self.repository.get_all()
