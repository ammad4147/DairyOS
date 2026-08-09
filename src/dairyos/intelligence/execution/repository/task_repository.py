class TaskRepository:
    """
    Repository interface for execution tasks.
    """

    def save(self, task):

        raise NotImplementedError

    def get_all(self):

        raise NotImplementedError
