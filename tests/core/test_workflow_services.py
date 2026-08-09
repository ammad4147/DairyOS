from dairyos.intelligence.workflow.services.workflow_service import (
    WorkflowService,
)

from dairyos.intelligence.workflow.services.workflow_execution_service import (
    WorkflowExecutionService,
)

from dairyos.intelligence.workflow.services.workflow_state_service import (
    WorkflowStateService,
)

from dairyos.intelligence.workflow.services.workflow_history_service import (
    WorkflowHistoryService,
)


def test_workflow_service_create():

    service = WorkflowService()

    workflow = service.create(
        workflow_type="feeding",
        description="Morning feeding workflow",
        initiated_by="decision_engine",
    )

    assert workflow.workflow_type == "feeding"
    assert workflow.description == "Morning feeding workflow"
    assert workflow.status == "pending"
    assert workflow.initiated_by == "decision_engine"


def test_execution_service_start():

    service = WorkflowExecutionService()

    execution = service.start(
        workflow_type="feeding",
        executed_by="farm_manager",
        notes="Workflow started",
    )

    assert execution.workflow_type == "feeding"
    assert execution.execution_status == "running"
    assert execution.executed_by == "farm_manager"
    assert execution.notes == "Workflow started"


def test_state_service_update():

    service = WorkflowStateService()

    state = service.update(
        workflow_type="feeding",
        current_state="completed",
        previous_state="running",
    )

    assert state.workflow_type == "feeding"
    assert state.current_state == "completed"
    assert state.previous_state == "running"


def test_history_service_record():

    service = WorkflowHistoryService()

    result = service.record(
        workflow_type="feeding",
        success=True,
        result="Workflow completed successfully",
        feedback="Execution successful",
    )

    assert result.workflow_type == "feeding"
    assert result.success is True
    assert result.result == "Workflow completed successfully"
    assert result.feedback == "Execution successful"
