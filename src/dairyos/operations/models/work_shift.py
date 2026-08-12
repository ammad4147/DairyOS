from dataclasses import dataclass
from datetime import time


@dataclass
class WorkShift:
    """Represents a scheduled farm work shift and task-board item."""

    shift_id: str
    name: str
    start_time: time
    end_time: time
    assigned_role: str
    task_category: str
    completed: bool = False
    status: str = "TODO"

    def start(self) -> None:
        self.status = "IN_PROGRESS"
        self.completed = False

    def complete(self) -> None:
        self.status = "COMPLETED"
        self.completed = True
