from dairyos.operations.accountability_integration.services.execution_accountability_bridge import (
    ExecutionAccountabilityBridge,
)


class FakeExecution:

    execution_id = "EXE-0001"

    assigned_to = "Milking Operator"



def test_execution_registers_accountability():

    bridge = ExecutionAccountabilityBridge()


    record = bridge.register_execution(
        FakeExecution(),
        "Morning Milking",
    )


    assert record.execution_id == "EXE-0001"

    assert record.staff_member == "Milking Operator"

    assert record.task_name == "Morning Milking"

    assert record.status == "ASSIGNED"
