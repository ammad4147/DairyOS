class WorkflowExecutionRepository:
    """
    Repository interface for workflow execution persistence.
    """

    def save(
        self,
        execution,
    ):
        raise NotImplementedError

    def get_all(
        self,
    ):
        raise NotImplementedError
