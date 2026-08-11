from dairyos.intelligence.operations.orchestration.models.execution_record import (
    ExecutionRecord,
)

from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)


def test_execution_record_from_execution_is_one_way_projection():
    execution = OperationalExecution(
        execution_id="EXE-TEST-001",
        action_id="health_check",
        assigned_to="veterinarian",
    )

    execution.complete(
        notes="Completed health inspection",
        actor="veterinarian",
    )

    record = ExecutionRecord.from_execution(
        execution=execution,
        performed_by="veterinarian",
        notes="Completed health inspection",
    )

    assert record.action_type == "health_check"
    assert record.performed_by == "veterinarian"
    assert record.execution_status == "completed"
    assert record.notes == "Completed health inspection"

    assert record.canonical_execution is execution
    assert record.canonical_execution.status == execution.COMPLETED

    assert not hasattr(record, "start")
    assert not hasattr(record, "complete")
    assert not hasattr(record, "verify")
    assert not hasattr(record, "close")
