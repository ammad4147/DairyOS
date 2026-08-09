from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class ExecutionMetric:
    """
    Represents workforce execution performance.

    Tracks completion lifecycle of
    operational assignments.
    """

    user_id: str

    action_id: str

    execution_status: str = "pending"

    metric_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    completed_at: datetime | None = None


    def complete(
        self,
    ):

        self.execution_status = "completed"

        self.completed_at = (
            datetime.now(
                timezone.utc
            )
        )
