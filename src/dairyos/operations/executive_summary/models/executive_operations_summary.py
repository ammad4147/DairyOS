from dataclasses import dataclass
from datetime import datetime

from .executive_priority import ExecutivePriority


@dataclass
class ExecutiveOperationsSummary:
    """
    Leadership summary of operations.
    """

    summary_id: str
    operational_health: str
    priority: ExecutivePriority
    key_message: str
    created_at: datetime
