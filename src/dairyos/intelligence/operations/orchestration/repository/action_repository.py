from abc import ABC, abstractmethod


class ActionRepository(ABC):
    """
    Repository abstraction for operational actions.
    """

    @abstractmethod
    def save(self, action):
        pass

    @abstractmethod
    def get_all(self):
        pass
