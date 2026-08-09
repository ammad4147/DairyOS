class KnowledgeRecordRepository:
    """
    Repository interface for enterprise knowledge records.
    """


    def save(
        self,
        record,
    ):

        raise NotImplementedError


    def get_all(
        self,
    ):

        raise NotImplementedError
