class QueueRepository:
    """
    Repository interface for execution queues.
    """

    def save(self, queue):

        raise NotImplementedError

    def get_all(self):

        raise NotImplementedError
