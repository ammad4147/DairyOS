class WorkflowResultRepository:
    """
    Repository interface for workflow result persistence.
    """

    def save(
        self,
        result,
    ):
        raise NotImplementedError

    def get_all(
        self,
    ):
        raise NotImplementedError
