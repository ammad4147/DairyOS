from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class HealthIndicator:
    component: str
    status: str
    message: str = ""
    timestamp: datetime = datetime.now(UTC)
