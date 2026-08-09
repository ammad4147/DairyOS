from dairyos.intelligence.memory.repository.context_repository import (
    ContextRepository,
)


class MemoryContextRepository(ContextRepository):
    """
    In-memory storage for memory contexts.
    """


    def __init__(
        self,
    ):

        self.contexts = []


    def save(
        self,
        context,
    ):

        self.contexts.append(
            context
        )

        return context


    def get_all(
        self,
    ):

        return self.contexts
