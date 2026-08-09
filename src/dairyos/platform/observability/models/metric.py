from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Metric:
    name: str
    value: float
    source: str
    timestamp: datetime = datetime.now(timezone.utc)
