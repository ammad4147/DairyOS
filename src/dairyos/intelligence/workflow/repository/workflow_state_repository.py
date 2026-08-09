class WorkflowStateRepository:
    """
    Repository interface for workflow state persistence.
    """

    def save(
        self,
        state,
    ):
        raise NotImplementedError

    def get_all(
        self,
    ):
        raise NotImplementedError
