from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DashboardActivity:
    """
    Dashboard read model for operational activity.

    Does not expose domain or database objects.
    """

    event_type: str

    source: str

    description: str

    timestamp: datetime
