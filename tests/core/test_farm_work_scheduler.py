from datetime import date, time

from dairyos.operations.models.work_shift import WorkShift
from dairyos.operations.services.farm_work_scheduler_service import (
    FarmWorkSchedulerService,
)


def test_create_schedule():

    service = FarmWorkSchedulerService()

    schedule = service.create_schedule(
        "SCH-001",
        date.today(),
        "Milking Shed",
    )

    assert schedule.schedule_id == "SCH-001"
    assert schedule.farm_area == "Milking Shed"


def test_add_shift():

    service = FarmWorkSchedulerService()

    schedule = service.create_schedule(
        "SCH-001",
        date.today(),
        "Milking Shed",
    )

    shift = WorkShift(
        shift_id="SHIFT-001",
        name="Morning Milking",
        start_time=time(5, 0),
        end_time=time(8, 0),
        assigned_role="Milker",
        task_category="Milking",
    )

    service.add_shift(
        "SCH-001",
        shift,
    )

    assert schedule.total_shifts() == 1


def test_complete_shift():

    service = FarmWorkSchedulerService()

    schedule = service.create_schedule(
        "SCH-001",
        date.today(),
        "Feed Area",
    )

    shift = WorkShift(
        shift_id="SHIFT-002",
        name="Morning Feeding",
        start_time=time(6, 0),
        end_time=time(7, 0),
        assigned_role="Farm Worker",
        task_category="Feeding",
    )

    service.add_shift(
        "SCH-001",
        shift,
    )

    service.complete_shift(
        "SCH-001",
        "SHIFT-002",
    )

    assert schedule.completed_shifts() == 1
    assert schedule.completion_percentage() == 100
