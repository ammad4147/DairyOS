from enum import Enum


class EventPriority(str, Enum):
    """
    Defines enterprise event urgency.
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
