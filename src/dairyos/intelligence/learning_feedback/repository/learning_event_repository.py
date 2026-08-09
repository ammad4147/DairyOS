class LearningEventRepository:
    """
    Repository interface for learning events.
    """

    def save(
        self,
        event,
    ):

        raise NotImplementedError


    def get_all(
        self,
    ):

        raise NotImplementedError
