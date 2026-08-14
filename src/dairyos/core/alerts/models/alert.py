from dataclasses import dataclass, field
from datetime import datetime
from dairyos.core.time_utils import utcnow


@dataclass
class Alert:

    event_type: str

    message: str

    priority: str

    created_at: datetime = field(default_factory=utcnow)