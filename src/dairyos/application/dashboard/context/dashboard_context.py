from dataclasses import dataclass
from uuid import UUID

from dairyos.application.identity.models.user_role import UserRole


@dataclass(frozen=True)
class DashboardContext:
    """
    Represents the operational context
    of a dashboard request.

    This identifies who is viewing
    the operational dashboard and
    under which farm responsibility role.
    """

    user_id: UUID
    user_name: str
    role: UserRole
