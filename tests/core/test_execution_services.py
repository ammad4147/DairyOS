from dairyos.intelligence.execution.services.execution_service import (
    ExecutionService,
)

from dairyos.intelligence.execution.services.task_dispatcher import (
    TaskDispatcher,
)

from dairyos.intelligence.execution.services.queue_manager import (
    QueueManager,
)

from dairyos.intelligence.execution.services.execution_monitor import (
    ExecutionMonitor,
)

from dairyos.intelligence.execution.services.execution_history_service import (
    ExecutionHistoryService,
)


def test_execution_service_create():

    service = ExecutionService()

    plan = service.create(
        workflow_type="health",
        objective="Treat mastitis",
        priority="high",
    )

    assert plan.status == "planned"


def test_task_dispatcher_dispatch():

    dispatcher = TaskDispatcher()

    task = dispatcher.dispatch(
        workflow_type="health",
        task_name="Inject Cow",
        assigned_to="Veterinarian",
    )

    assert task.status == "assigned"


def test_queue_manager_create():

    manager = QueueManager()

    queue = manager.create(
        workflow_type="health",
        queue_name="Morning Queue",
        pending_tasks=4,
    )

    assert queue.status == "active"


def test_execution_monitor_update():

    monitor = ExecutionMonitor()

    status = monitor.update(
        workflow_type="health",
        current_status="running",
        previous_status="planned",
    )

    assert status.current_status == "running"


def test_execution_history_record():

    history = ExecutionHistoryService()

    result = history.record(
        workflow_type="health",
        success=True,
        result="Completed",
        feedback="Successful",
    )

    assert result.success is True
