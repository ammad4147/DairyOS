from dairyos.intelligence.memory.models.memory_record import (
    MemoryRecord,
)


class MemoryService:
    """
    Manages intelligence memory records.

    Future extensions:

    - memory ranking
    - semantic retrieval
    - memory lifecycle
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository


    def create(
        self,
        memory_id: str,
        memory_type: str,
        content: str,
        source: str,
        confidence: float,
    ) -> MemoryRecord:

        memory = MemoryRecord(
            memory_id=memory_id,
            memory_type=memory_type,
            content=content,
            source=source,
            confidence=confidence,
        )

        return self.repository.save(
            memory
        )
