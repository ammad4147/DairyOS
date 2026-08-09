from dataclasses import dataclass, field
from datetime import date
from typing import List

from .work_shift import WorkShift


@dataclass
class WorkSchedule:
    """
    Represents a daily farm operational schedule.
    """

    schedule_id: str
    schedule_date: date
    farm_area: str
    shifts: List[WorkShift] = field(default_factory=list)

    def add_shift(self, shift: WorkShift) -> None:
        self.shifts.append(shift)

    def completed_shifts(self) -> int:
        return sum(
            1 for shift in self.shifts
            if shift.completed
        )

    def total_shifts(self) -> int:
        return len(self.shifts)

    def completion_percentage(self) -> float:
        if not self.shifts:
            return 0.0

        return (
            self.completed_shifts()
            / self.total_shifts()
        ) * 100
