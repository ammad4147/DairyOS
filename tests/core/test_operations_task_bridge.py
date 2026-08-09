from dairyos.operations.models.daily_operation import DailyOperation
from dairyos.operations.services import OperationsTaskBridge


def test_create_staff_task():

    operation = DailyOperation(
        operation_id="OP-001",
        operation_type="FEEDING",
        description="Morning Feeding",
    )

    bridge = OperationsTaskBridge()

    task = bridge.create_staff_task(
        operation,
        assigned_team="Feeding Team",
        urgency="high",
    )

    assert task.task_id == "OP-001"
    assert task.task_name == "Morning Feeding"
    assert task.assigned_team == "Feeding Team"
    assert task.priority == "HIGH"
    assert task.status == "PENDING"


def test_medium_priority():

    operation = DailyOperation(
        operation_id="OP-002",
        operation_type="MILKING",
        description="Morning Milking",
    )

    bridge = OperationsTaskBridge()

    task = bridge.create_staff_task(
        operation,
        assigned_team="Milking Team",
    )

    assert task.priority == "MEDIUM"
    assert task.status == "SCHEDULED"


def test_low_priority():

    operation = DailyOperation(
        operation_id="OP-003",
        operation_type="CLEANING",
        description="Wash Feed Alley",
    )

    bridge = OperationsTaskBridge()

    task = bridge.create_staff_task(
        operation,
        assigned_team="Maintenance",
        urgency="low",
    )

    assert task.priority == "NORMAL"
    assert task.status == "PLANNED"