class ExecutionRepository:
    """
    Repository interface for execution plans.
    """

    def save(self, execution):

        raise NotImplementedError

    def get_all(self):

        raise NotImplementedError
