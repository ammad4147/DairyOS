from dataclasses import dataclass
from datetime import datetime


@dataclass
class Alert:

    event_type: str

    message: str

    priority: str

    created_at: datetime = datetime.utcnow()
