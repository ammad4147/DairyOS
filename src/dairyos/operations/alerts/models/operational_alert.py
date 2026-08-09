from dataclasses import dataclass
from datetime import datetime

from .alert_severity import AlertSeverity


@dataclass
class OperationalAlert:
    """
    Represents an operational issue requiring attention.
    """

    alert_id: str
    title: str
    severity: AlertSeverity
    description: str
    created_at: datetime
    resolved: bool = False
