class WorkflowHistoryRepository:
    """
    Repository interface for workflow history persistence.
    """

    def save(
        self,
        history,
    ):
        raise NotImplementedError

    def get_all(
        self,
    ):
        raise NotImplementedError
