from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class FeedSignalType(str, Enum):
    LOW_CONSUMPTION = "LOW_CONSUMPTION"
    HIGH_CONSUMPTION = "HIGH_CONSUMPTION"
    INTAKE_VARIANCE = "INTAKE_VARIANCE"
    FEEDING_DELAY = "FEEDING_DELAY"
    FEED_WASTE = "FEED_WASTE"


class FeedSignalSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class FeedSignal:
    signal_type: FeedSignalType
    severity: FeedSignalSeverity
    animal_group: str
    expected_intake: float
    actual_intake: float
    variance_percentage: float
    message: str

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    resolved: bool = False

    def resolve(self):
        self.resolved = True
