from datetime import date

from ..models.work_shift import WorkShift
from ..models.work_schedule import WorkSchedule


class FarmWorkSchedulerService:
    """
    Service responsible for managing daily farm work schedules.
    """

    def __init__(self):
        self.schedules = {}

    def create_schedule(
        self,
        schedule_id: str,
        schedule_date: date,
        farm_area: str,
    ) -> WorkSchedule:

        schedule = WorkSchedule(
            schedule_id=schedule_id,
            schedule_date=schedule_date,
            farm_area=farm_area,
        )

        self.schedules[schedule_id] = schedule

        return schedule

    def add_shift(
        self,
        schedule_id: str,
        shift: WorkShift,
    ) -> WorkSchedule:

        schedule = self.schedules[schedule_id]

        schedule.add_shift(shift)

        return schedule

    def complete_shift(
        self,
        schedule_id: str,
        shift_id: str,
    ) -> WorkSchedule:

        schedule = self.schedules[schedule_id]

        for shift in schedule.shifts:
            if shift.shift_id == shift_id:
                shift.complete()
                break

        return schedule

    def get_schedule(
        self,
        schedule_id: str,
    ) -> WorkSchedule | None:

        return self.schedules.get(schedule_id)

    def list_schedules(self):
        return list(self.schedules.values())
