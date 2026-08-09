class WorkflowRepository:
    """
    Repository interface for workflow persistence.
    """

    def save(
        self,
        workflow,
    ):
        raise NotImplementedError

    def get_all(
        self,
    ):
        raise NotImplementedError
