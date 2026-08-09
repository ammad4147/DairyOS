from dairyos.operations.execution.services.execution_lifecycle_bridge import (
    ExecutionLifecycleBridge,
)


class FakeExecution:

    execution_id = "EXE-0001"

    action_id = "ACT-0001"



def test_execution_lifecycle_flow():

    bridge = ExecutionLifecycleBridge()


    outcome = bridge.record_execution_outcome(

        FakeExecution(),

        95,

        "Completed successfully",

    )


    assert outcome.status.value == "SUCCESSFUL"


    verification = bridge.verify_execution(

        FakeExecution(),

        True,

        "Verified by supervisor",

    )


    assert verification.status.value == "VERIFIED"


    closure = bridge.assess_closure(

        FakeExecution(),

        "Morning Milking",

        True,

        95,

    )


    assert closure.closure_status == "SUCCESS"
