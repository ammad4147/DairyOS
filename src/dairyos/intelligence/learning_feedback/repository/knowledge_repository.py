class KnowledgeRepository:
    """
    Repository interface for knowledge adjustments.
    """

    def save(
        self,
        knowledge,
    ):

        raise NotImplementedError


    def get_all(
        self,
    ):

        raise NotImplementedError
