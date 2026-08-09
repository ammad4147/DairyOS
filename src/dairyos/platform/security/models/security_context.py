from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class SecurityContext:
    """
    Represents the authenticated execution context.

    Every protected DairyOS operation can carry
    this security identity boundary.
    """

    user_id: str
    username: str

    roles: list[str] = field(
        default_factory=list
    )

    permissions: list[str] = field(
        default_factory=list
    )

    session_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def has_permission(
        self,
        permission: str
    ) -> bool:
        return permission in self.permissions
