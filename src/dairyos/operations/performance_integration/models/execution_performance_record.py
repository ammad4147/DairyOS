from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ExecutionPerformanceRecord:
    """
    Represents measurable execution performance.
    """

    execution_id: str

    staff_member: str

    task_name: str

    completion_status: str

    performance_score: float

    recorded_at: datetime = (
        datetime.now(timezone.utc)
    )
