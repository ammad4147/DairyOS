from abc import ABC, abstractmethod


class MemoryRepository(ABC):
    """
    Repository interface for memory records.
    """


    @abstractmethod
    def save(
        self,
        memory,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ):
        pass
