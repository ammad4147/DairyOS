from dairyos.operations.command_execution.services.command_execution_service import (
    CommandExecutionService,
)

from dairyos.operations.command_execution.services.execution_tracking_service import (
    ExecutionTrackingService,
)

from dairyos.operations.command_execution.models.execution_status import (
    ExecutionStatus,
)



def test_create_command_execution():

    service = CommandExecutionService()


    execution = service.create_execution(
        "EXEC-001",
        "CMD-001",
        "Farm Supervisor",
    )


    assert execution.status == ExecutionStatus.CREATED



def test_complete_command_execution():

    service = CommandExecutionService()


    execution = service.create_execution(
        "EXEC-002",
        "CMD-002",
        "Veterinarian",
    )


    tracker = ExecutionTrackingService()

    tracker.start(execution)

    tracker.complete(execution)


    assert execution.status == ExecutionStatus.COMPLETED
