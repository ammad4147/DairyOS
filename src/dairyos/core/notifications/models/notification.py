from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Notification:

    recipient: str

    message: str

    priority: str = "INFO"

    status: str = "NEW"

    created_at: datetime = field(
        default_factory=datetime.utcnow
    )
