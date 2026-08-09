from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class HeadsUpNotification:

    notification_type: str

    message: str

    severity: str = "INFO"

    created_at: datetime = field(
        default_factory=lambda:
        datetime.now(timezone.utc)
    )
