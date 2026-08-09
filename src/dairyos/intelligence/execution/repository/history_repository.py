class HistoryRepository:
    """
    Repository interface for execution history.
    """

    def save(self, record):

        raise NotImplementedError

    def get_all(self):

        raise NotImplementedError
