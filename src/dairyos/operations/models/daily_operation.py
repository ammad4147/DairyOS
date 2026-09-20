from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DailyOperation:
    """
    Represents a daily farm operational activity.

    Examples:
    - Feeding
    - Milking
    - Health Check
    - Cleaning
    - Maintenance
    """

    operation_id: str
    operation_type: str
    description: str

    status: str = "PENDING"
    completed_at: datetime | None = None
    completion_notes: str | None = None

    created_at: datetime = field(
        default_factory=datetime.now
    )

    def complete(self, notes: str | None = None) -> None:
        """
        Mark operation as completed.
        """

        self.status = "COMPLETED"
        self.completed_at = datetime.now()
        self.completion_notes = notes

    def is_completed(self) -> bool:
        """
        Check whether operation is completed.
        """

        return self.status == "COMPLETED"