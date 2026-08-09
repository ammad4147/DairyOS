from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from dairyos.operations.execution.services.execution_tracking_service import (
    ExecutionTrackingService,
)

from dairyos.operations.workflow.services.execution_workflow_bridge import (
    ExecutionWorkflowBridge,
)



def test_operational_execution_lifecycle():

    execution_service = OperationalExecutionService()

    execution = execution_service.create_execution(
        action_id="ACT-0001",
        assigned_to="Milking Operator",
    )


    tracker = ExecutionTrackingService()


    assert execution.status == "CREATED"


    tracker.start(execution)

    assert execution.status == "STARTED"
    assert execution.started_at is not None


    tracker.complete(
        execution,
        notes="Morning milking completed",
    )

    assert execution.status == "COMPLETED"
    assert execution.completed_at is not None


    tracker.verify(execution)

    assert execution.status == "VERIFIED"
    assert execution.verified_at is not None



def test_execution_workflow_summary():

    execution_service = OperationalExecutionService()

    execution = execution_service.create_execution(
        action_id="ACT-0002",
        assigned_to="Feed Supervisor",
    )


    tracker = ExecutionTrackingService()

    tracker.complete(execution)


    bridge = ExecutionWorkflowBridge()

    summary = bridge.execution_summary(
        execution
    )


    assert summary["execution_id"] == execution.execution_id
    assert summary["action_id"] == "ACT-0002"
    assert summary["completed"] is True
