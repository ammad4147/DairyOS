from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)

from dairyos.operations.execution.services.execution_tracking_service import (
    ExecutionTrackingService,
)


def test_execution_human_lifecycle():

    execution = OperationalExecution(
        execution_id="EXE-0001",
        action_id="ACT-0001",
        assigned_to="Farm Supervisor",
    )

    service = ExecutionTrackingService()


    service.assign(execution)

    assert execution.status == "ASSIGNED"


    service.acknowledge(
        execution,
        "Farm Supervisor",
    )

    assert execution.status == "ACKNOWLEDGED"


    service.start(
        execution,
        "Farm Supervisor",
    )

    assert execution.status == "STARTED"


    service.complete(
        execution,
        "Task completed",
        "Farm Supervisor",
    )

    assert execution.status == "COMPLETED"


    service.verify(
        execution,
        "Farm Manager",
    )

    assert execution.status == "VERIFIED"


    service.close(execution)

    assert execution.status == "CLOSED"
