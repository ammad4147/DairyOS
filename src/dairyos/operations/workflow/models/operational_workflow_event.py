from dataclasses import dataclass
from datetime import datetime


@dataclass
class OperationalWorkflowEvent:
    """
    Represents an operational event moving through the DairyOS workflow.
    """

    event_id: str
    source: str
    category: str
    priority: str
    description: str
    created_at: datetime
