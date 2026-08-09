from enum import Enum


class AlertSeverity(Enum):
    """
    Operational alert severity levels.
    """

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
