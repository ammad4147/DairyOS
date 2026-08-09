from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class WorkflowProjection:
    """
    Intelligence read model for operational workflows.
    """

    workflow_id: str

    workflow_type: str

    assigned_to: str

    status: str

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    started_at: datetime | None = None

    completed_at: datetime | None = None


    def duration_seconds(self):
        if not self.started_at or not self.completed_at:
            return None

        return (
            self.completed_at - self.started_at
        ).total_seconds()
