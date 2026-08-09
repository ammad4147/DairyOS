from dairyos.intelligence.workflow.models.workflow import (
    Workflow,
)

from dairyos.intelligence.workflow.models.workflow_step import (
    WorkflowStep,
)

from dairyos.intelligence.workflow.models.workflow_state import (
    WorkflowState,
)

from dairyos.intelligence.workflow.models.workflow_execution import (
    WorkflowExecution,
)

from dairyos.intelligence.workflow.models.workflow_result import (
    WorkflowResult,
)

from dairyos.intelligence.workflow.models.workflow_context import (
    WorkflowContext,
)


def test_workflow_creation():

    workflow = Workflow(
        workflow_type="feeding",
        description="Morning feeding workflow",
        status="pending",
        initiated_by="decision_engine",
    )

    assert workflow.workflow_type == "feeding"
    assert workflow.description == "Morning feeding workflow"
    assert workflow.status == "pending"
    assert workflow.initiated_by == "decision_engine"


def test_workflow_step_creation():

    step = WorkflowStep(
        workflow_type="feeding",
        step_name="Prepare Feed",
        sequence=1,
        status="pending",
    )

    assert step.workflow_type == "feeding"
    assert step.step_name == "Prepare Feed"
    assert step.sequence == 1
    assert step.status == "pending"


def test_workflow_state_creation():

    state = WorkflowState(
        workflow_type="feeding",
        current_state="running",
        previous_state="pending",
    )

    assert state.workflow_type == "feeding"
    assert state.current_state == "running"
    assert state.previous_state == "pending"


def test_workflow_execution_creation():

    execution = WorkflowExecution(
        workflow_type="feeding",
        execution_status="completed",
        executed_by="farm_manager",
        notes="Executed successfully",
    )

    assert execution.workflow_type == "feeding"
    assert execution.execution_status == "completed"
    assert execution.executed_by == "farm_manager"
    assert execution.notes == "Executed successfully"


def test_workflow_result_creation():

    result = WorkflowResult(
        workflow_type="feeding",
        success=True,
        result="Workflow completed",
        feedback="All steps executed",
    )

    assert result.workflow_type == "feeding"
    assert result.success is True
    assert result.result == "Workflow completed"
    assert result.feedback == "All steps executed"


def test_workflow_context_creation():

    context = WorkflowContext(
        workflow_type="feeding",
        initiated_by="decision_engine",
    )

    assert context.workflow_type == "feeding"
    assert context.initiated_by == "decision_engine"
    assert context.created_at is not None
