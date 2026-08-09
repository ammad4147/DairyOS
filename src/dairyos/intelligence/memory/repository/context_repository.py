from abc import ABC, abstractmethod


class ContextRepository(ABC):
    """
    Repository interface for memory contexts.
    """


    @abstractmethod
    def save(
        self,
        context,
    ):
        pass


    @abstractmethod
    def get_all(
        self,
    ):
        pass
