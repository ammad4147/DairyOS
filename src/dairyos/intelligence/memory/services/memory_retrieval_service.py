class MemoryRetrievalService:
    """
    Retrieves intelligence memories.

    Future extensions:

    - semantic search
    - relevance ranking
    - vector database integration
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository


    def retrieve_all(
        self,
    ):

        return self.repository.get_all()
