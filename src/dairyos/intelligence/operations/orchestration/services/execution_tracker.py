from dairyos.intelligence.operations.orchestration.models.execution_record import (
    ExecutionRecord,
)
from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)
from dairyos.operations.execution.services.execution_tracking_service import (
    ExecutionTrackingService,
)


class ExecutionTracker:
    """
    Compatibility tracker for orchestration callers.

    ExecutionRecord remains a historical/outcome DTO. The authoritative
    execution lifecycle is created and completed through
    OperationalExecution and ExecutionTrackingService.
    """

    def __init__(self, execution_service=None, tracking_service=None):
        self.execution_service = execution_service or OperationalExecutionService()
        self.tracking_service = tracking_service or ExecutionTrackingService()

    def record_execution(
        self,
        action_type: str,
        performed_by: str,
        notes: str = "",
    ) -> ExecutionRecord:
        execution = self.execution_service.create_execution(
            action_id=action_type,
            assigned_to=performed_by,
        )

        self.tracking_service.complete(
            execution,
            notes=notes,
            actor=performed_by,
        )

        return ExecutionRecord(
            action_type=action_type,
            performed_by=performed_by,
            execution_status=execution.status.lower(),
            notes=notes,
        )
