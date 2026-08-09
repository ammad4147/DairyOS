from dataclasses import dataclass
from uuid import UUID

from .user_role import UserRole


@dataclass(frozen=True)
class UserSession:
    """
    Represents the active operational session
    of a DairyOS user.

    Authentication identity is external.

    This object represents the operational
    responsibility context after login.
    """


    user_id: UUID

    user_name: str

    role: UserRole

    active: bool = True
