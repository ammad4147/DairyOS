from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class PlatformContext:
    """
    Represents the active DairyOS enterprise platform runtime.
    """

    platform_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    environment: str = "development"

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    active: bool = True
