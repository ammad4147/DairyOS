from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class WorkforceAccountabilitySnapshot:
    """
    Represents workforce accountability intelligence.

    Measures ownership of operational responsibilities.
    """

    total_tasks: int

    completed_tasks: int

    pending_tasks: int

    overdue_tasks: int

    accountability_score: float

    accountability_status: str

    escalation_required: bool

    generated_at: datetime = datetime.now(timezone.utc)
