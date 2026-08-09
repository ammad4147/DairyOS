from dairyos.intelligence.execution.models.execution_plan import (
    ExecutionPlan,
)

from dairyos.intelligence.execution.models.execution_task import (
    ExecutionTask,
)

from dairyos.intelligence.execution.models.execution_queue import (
    ExecutionQueue,
)

from dairyos.intelligence.execution.models.execution_status import (
    ExecutionStatus,
)

from dairyos.intelligence.execution.models.execution_result import (
    ExecutionResult,
)

from dairyos.intelligence.execution.models.execution_log import (
    ExecutionLog,
)


def test_execution_plan_creation():

    plan = ExecutionPlan(
        workflow_type="health",
        objective="Treat mastitis",
        priority="high",
        status="planned",
    )

    assert plan.workflow_type == "health"
    assert plan.status == "planned"


def test_execution_task_creation():

    task = ExecutionTask(
        workflow_type="health",
        task_name="Inject Cow",
        assigned_to="Vet",
        status="assigned",
    )

    assert task.task_name == "Inject Cow"


def test_execution_queue_creation():

    queue = ExecutionQueue(
        workflow_type="health",
        queue_name="Morning Queue",
        pending_tasks=5,
        status="active",
    )

    assert queue.pending_tasks == 5


def test_execution_status_creation():

    status = ExecutionStatus(
        workflow_type="health",
        current_status="running",
        previous_status="planned",
    )

    assert status.current_status == "running"


def test_execution_result_creation():

    result = ExecutionResult(
        workflow_type="health",
        success=True,
        result="Completed",
        feedback="Normal",
    )

    assert result.success


def test_execution_log_creation():

    log = ExecutionLog(
        workflow_type="health",
        message="Started",
        recorded_by="System",
    )

    assert log.recorded_by == "System"
