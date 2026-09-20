from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class ExecutionAccountability:
    """
    Represents staff accountability for executed work.
    """

    execution_id: str

    staff_member: str

    task_name: str

    status: str = "ASSIGNED"

    assigned_at: datetime = (
        datetime.now(UTC)
    )

    completed_at: datetime | None = None


    def complete(self):

        self.status = "COMPLETED"

        self.completed_at = (
            datetime.now(UTC)
        )
