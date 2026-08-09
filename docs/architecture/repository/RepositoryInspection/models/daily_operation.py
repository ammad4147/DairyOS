from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


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
    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None

    created_at: datetime = field(
        default_factory=datetime.now
    )

    def complete(self, notes: Optional[str] = None) -> None:
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