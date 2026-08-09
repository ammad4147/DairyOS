from datetime import datetime, timezone


from dairyos.operations.accountability_integration.services.accountability_bridge import (
    AccountabilityBridge,
)


class FakeExecution:

    execution_id = "EXE-0001"

    assigned_to = "Milking Operator"



def test_execution_creates_accountability_record():

    bridge = AccountabilityBridge()


    execution = FakeExecution()


    record = bridge.create_accountability_record(
        execution,
        "Morning Milking",
    )


    assert record.execution_id == "EXE-0001"

    assert record.staff_member == "Milking Operator"

    assert record.task_name == "Morning Milking"

    assert record.status == "ASSIGNED"



def test_accountability_completion():

    bridge = AccountabilityBridge()


    execution = FakeExecution()


    record = bridge.create_accountability_record(
        execution,
        "Feed Distribution",
    )


    record.complete()


    assert record.status == "COMPLETED"

    assert record.completed_at is not None
