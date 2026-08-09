from dairyos.intelligence.memory.models.memory_context import (
    MemoryContext,
)


class ContextManager:
    """
    Manages intelligence memory context.

    Future extensions:

    - context inheritance
    - context resolution
    - context expiration
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository


    def create(
        self,
        context_id: str,
        context_type: str,
        description: str,
        owner: str,
    ) -> MemoryContext:

        context = MemoryContext(
            context_id=context_id,
            context_type=context_type,
            description=description,
            owner=owner,
        )

        return self.repository.save(
            context
        )
