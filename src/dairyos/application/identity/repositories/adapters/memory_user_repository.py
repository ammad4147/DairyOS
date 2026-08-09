from uuid import UUID

from ..user_repository import UserRepository


class MemoryUserRepository(UserRepository):
    """
    In-memory operational user repository.

    Used for application runtime and testing.
    """

    def __init__(self):
        self.items = {}

    def save(self, user):

        self.items[user.user_id] = user

        return user

    def get(self, user_id: UUID):

        return self.items.get(user_id)

    def list_all(self):

        return list(self.items.values())
