class MemoryRepository:
    """
    Repository interface for learning memory.
    """

    def save(
        self,
        memory,
    ):

        raise NotImplementedError


    def get_all(
        self,
    ):

        raise NotImplementedError
