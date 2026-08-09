from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class TaskExecutionResult:
    """
    Result returned after operational task execution.
    """

    task_id: str

    task_type: str

    success: bool

    result: object | None = None

    executed_at: datetime = datetime.now(
        timezone.utc
    )
