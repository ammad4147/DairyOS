from dataclasses import dataclass
from uuid import UUID

from .user_role import UserRole


@dataclass(frozen=True)
class OperationalUser:
    """
    Represents a farm operational user.

    Authentication is intentionally outside this model.
    This represents operational responsibility context.
    """

    user_id: UUID
    name: str
    role: UserRole
    active: bool = True
