from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class WorkforceExecutionSnapshot:
    """
    Operational workforce intelligence snapshot.

    Provides management visibility
    into workforce execution performance.
    """


    total_assignments: int

    completed_assignments: int

    pending_assignments: int

    completion_rate: float

    execution_health: str

    attention_required: bool

    generated_at: datetime = (
        datetime.now(timezone.utc)
    )
