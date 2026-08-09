from abc import ABC, abstractmethod


class ExecutionRepository(ABC):
    """
    Repository abstraction for execution records.
    """

    @abstractmethod
    def save(self, record):
        pass

    @abstractmethod
    def get_all(self):
        pass
