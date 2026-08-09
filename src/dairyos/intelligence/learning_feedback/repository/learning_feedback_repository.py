class LearningFeedbackRepository:
    """
    Repository interface for learning feedback.
    """

    def save(
        self,
        feedback,
    ):

        raise NotImplementedError


    def get_all(
        self,
    ):

        raise NotImplementedError
