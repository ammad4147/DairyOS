from abc import ABC, abstractmethod


class AssignmentRepository(ABC):
    """
    Repository abstraction for action assignments.
    """

    @abstractmethod
    def save(self, assignment):
        pass

    @abstractmethod
    def get_all(self):
        pass
