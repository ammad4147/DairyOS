from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from .role import Role


@dataclass
class User:
    """
    Represents an enterprise user
    within DairyOS.
    """

    username: str

    display_name: str = ""

    user_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    role: Role | None = None

    email: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    active: bool = True
