from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class WorkforcePerformanceSnapshot:
    """
    Represents workforce execution performance intelligence.
    """

    total_tasks: int

    completed_tasks: int

    pending_tasks: int

    completion_rate: float

    reliability_score: float

    performance_status: str

    attention_required: bool

    generated_at: datetime = (
        datetime.now(timezone.utc)
    )
