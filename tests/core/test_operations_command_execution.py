from dairyos.operations.command_execution.models.execution_status import (
    ExecutionStatus,
)

from dairyos.operations.command_execution.services.command_execution_service import (
    CommandExecutionService,
)

from dairyos.operations.command_execution.services.execution_tracking_service import (
    ExecutionTrackingService,
)


def test_create_command_execution_is_backed_by_canonical_execution():
    service = CommandExecutionService()

    execution = service.create_execution(
        "EXEC-001",
        "CMD-001",
        "Farm Supervisor",
    )

    assert execution.execution_id == "EXEC-001"
    assert execution.command_id == "CMD-001"
    assert execution.assigned_to == "Farm Supervisor"
    assert execution.status == ExecutionStatus.CREATED

    canonical = execution.canonical_execution

    assert canonical is not None
    assert canonical.action_id == "CMD-001"
    assert canonical.assigned_to == "Farm Supervisor"
    assert canonical.status == canonical.CREATED


def test_start_command_execution_transitions_canonical_execution():
    service = CommandExecutionService()

    execution = service.create_execution(
        "EXEC-002",
        "CMD-002",
        "Veterinarian",
    )

    tracker = ExecutionTrackingService()

    tracker.start(execution)

    assert execution.status == ExecutionStatus.IN_PROGRESS

    canonical = execution.canonical_execution

    assert canonical is not None
    assert canonical.status == canonical.STARTED
    assert canonical.started_at is not None


def test_complete_command_execution_transitions_canonical_execution():
    service = CommandExecutionService()

    execution = service.create_execution(
        "EXEC-003",
        "CMD-003",
        "Veterinarian",
    )

    tracker = ExecutionTrackingService()

    tracker.start(execution)
    tracker.complete(execution)

    assert execution.status == ExecutionStatus.COMPLETED

    canonical = execution.canonical_execution

    assert canonical is not None
    assert canonical.status == canonical.COMPLETED
    assert canonical.completed_at is not None


def test_failed_command_execution_does_not_create_competing_canonical_lifecycle():
    service = CommandExecutionService()

    execution = service.create_execution(
        "EXEC-004",
        "CMD-004",
        "Farm Supervisor",
    )

    tracker = ExecutionTrackingService()

    tracker.failed(execution)

    assert execution.status == ExecutionStatus.FAILED

    canonical = execution.canonical_execution

    assert canonical is not None

    # FAILED is a legacy command/outcome projection only.
    # It must not become a second OperationalExecution lifecycle state.
    assert canonical.status == canonical.CREATED
