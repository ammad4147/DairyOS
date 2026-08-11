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

    ExecutionTracker does not own execution state.

    It translates the legacy record_execution() operation into the
    canonical operational execution lifecycle:

        ExecutionTracker
              |
              v
        OperationalExecutionService
              |
              v
        OperationalExecution
              |
              v
        ExecutionTrackingService.complete()
              |
              v
        ExecutionRecord projection

    ExecutionRecord is therefore an outcome/history projection only.
    """

    def __init__(
        self,
        execution_service=None,
        tracking_service=None,
    ):
        self.execution_service = (
            execution_service
            or OperationalExecutionService()
        )

        self.tracking_service = (
            tracking_service
            or ExecutionTrackingService()
        )

    def record_execution(
        self,
        action_type: str,
        performed_by: str,
        notes: str = "",
    ) -> ExecutionRecord:
        """
        Record completed work through the canonical execution path.

        This method intentionally preserves the legacy API while
        eliminating ExecutionRecord as an execution authority.
        """

        execution = self.execution_service.create_execution(
            action_id=action_type,
            assigned_to=performed_by,
        )

        self.tracking_service.complete(
            execution,
            notes=notes,
            actor=performed_by,
        )

        return ExecutionRecord.from_execution(
            execution=execution,
            performed_by=performed_by,
            notes=notes,
        )
