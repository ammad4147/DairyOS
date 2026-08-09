from abc import ABC, abstractmethod


class OutcomeRepository(ABC):
    """
    Repository abstraction for action outcomes.
    """

    @abstractmethod
    def save(self, outcome):
        pass

    @abstractmethod
    def get_all(self):
        pass
