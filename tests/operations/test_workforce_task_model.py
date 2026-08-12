from datetime import time

from dairyos.operations.models.work_shift import WorkShift


def test_work_shift_starts_in_todo_state():
    shift = WorkShift(
        shift_id="WS-1",
        name="Morning milking",
        start_time=time(5, 0),
        end_time=time(8, 0),
        assigned_role="MILKER",
        task_category="MILKING",
    )

    assert shift.status == "TODO"
    assert shift.completed is False


def test_work_shift_can_move_to_in_progress_and_completed():
    shift = WorkShift(
        shift_id="WS-1",
        name="Morning milking",
        start_time=time(5, 0),
        end_time=time(8, 0),
        assigned_role="MILKER",
        task_category="MILKING",
    )

    shift.start()
    assert shift.status == "IN_PROGRESS"
    assert shift.completed is False

    shift.complete()
    assert shift.status == "COMPLETED"
    assert shift.completed is True
