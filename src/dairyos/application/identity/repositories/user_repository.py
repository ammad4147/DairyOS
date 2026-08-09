from abc import ABC, abstractmethod

from ..models.operational_user import OperationalUser


class UserRepository(ABC):
    """
    Repository abstraction for operational users.
    """

    @abstractmethod
    def save(self, user: OperationalUser) -> OperationalUser:
        pass

    @abstractmethod
    def get(self, user_id):
        pass

    @abstractmethod
    def list_all(self):
        pass
