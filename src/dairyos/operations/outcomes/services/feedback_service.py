from ..models.outcome_feedback import OutcomeFeedback


class FeedbackService:
    """
    Captures operational improvement feedback.
    """

    def create_feedback(
        self,
        worked: str,
        failed: str,
        improvement: str,
    ) -> OutcomeFeedback:

        return OutcomeFeedback(
            what_worked=worked,
            what_failed=failed,
            improvement=improvement,
        )

