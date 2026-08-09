from dataclasses import dataclass
from datetime import time


@dataclass
class WorkShift:
    """
    Represents a scheduled farm work shift.
    """

    shift_id: str
    name: str
    start_time: time
    end_time: time
    assigned_role: str
    task_category: str
    completed: bool = False

    def complete(self) -> None:
        self.completed = True
