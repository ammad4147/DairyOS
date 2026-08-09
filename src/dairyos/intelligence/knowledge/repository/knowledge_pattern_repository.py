class KnowledgePatternRepository:
    """
    Repository interface for knowledge patterns.

    Future extensions:

    - PostgreSQL persistence
    - vector search
    - semantic retrieval
    """


    def save(
        self,
        pattern,
    ):

        raise NotImplementedError


    def get_all(
        self,
    ):

        raise NotImplementedError
