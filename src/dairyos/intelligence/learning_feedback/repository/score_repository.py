class ScoreRepository:
    """
    Repository interface for learning scores.
    """

    def save(
        self,
        score,
    ):

        raise NotImplementedError


    def get_all(
        self,
    ):

        raise NotImplementedError
