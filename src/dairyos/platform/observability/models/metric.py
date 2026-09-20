from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class Metric:
    name: str
    value: float
    source: str
    timestamp: datetime = datetime.now(UTC)
