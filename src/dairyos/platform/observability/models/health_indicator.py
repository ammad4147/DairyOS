from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class HealthIndicator:
    component: str
    status: str
    message: str = ""
    timestamp: datetime = datetime.now(timezone.utc)
