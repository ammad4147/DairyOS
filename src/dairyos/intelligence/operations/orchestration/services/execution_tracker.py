from dairyos.intelligence.operations.orchestration.models.execution_record import (
    ExecutionRecord,
)


class ExecutionTracker:
    """
    Tracks operational action execution.
    """

    def record_execution(
        self,
        action_type: str,
        performed_by: str,
        notes: str = "",
    ) -> ExecutionRecord:

        return ExecutionRecord(
            action_type=action_type,
            performed_by=performed_by,
            execution_status="completed",
            notes=notes,
        )
