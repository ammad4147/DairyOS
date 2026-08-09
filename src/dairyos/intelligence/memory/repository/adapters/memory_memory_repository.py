from dairyos.intelligence.memory.repository.memory_repository import (
    MemoryRepository,
)


class MemoryMemoryRepository(MemoryRepository):
    """
    In-memory storage for memory records.
    """


    def __init__(
        self,
    ):

        self.records = []


    def save(
        self,
        memory,
    ):

        self.records.append(
            memory
        )

        return memory


    def get_all(
        self,
    ):

        return self.records
