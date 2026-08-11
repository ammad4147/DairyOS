from dairyos.operations.execution.services.execution_tracking_service import (
    ExecutionTrackingService as OperationalExecutionTrackingService,
)
from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from ..models.execution_status import ExecutionStatus


class ExecutionTrackingService:
    """
    Compatibility facade for the legacy command-execution tracker.

    The legacy CommandExecution object is no longer an independent
    execution state machine. Lifecycle changes are delegated to the
    canonical OperationalExecution aggregate.
    """

    def __init__(self, execution_service=None, tracking_service=None):
        self.execution_service = execution_service or OperationalExecutionService()
        self.tracking_service = (
            tracking_service
            or OperationalExecutionTrackingService()
        )

    def _canonical(self, execution):
        canonical = getattr(execution, "_canonical_execution", None)
        if canonical is not None:
            return canonical

        canonical = self.execution_service.create_execution(
            action_id=execution.command_id,
            assigned_to=execution.assigned_to,
        )
        execution._canonical_execution = canonical
        return canonical

    def start(self, execution):
        canonical = self._canonical(execution)
        self.tracking_service.start(canonical)
        execution.status = ExecutionStatus.IN_PROGRESS
        return execution

    def complete(self, execution):
        canonical = self._canonical(execution)
        self.tracking_service.complete(canonical)
        execution.status = ExecutionStatus.COMPLETED
        return execution

    def failed(self, execution):
        # Failure remains a compatibility result in the legacy DTO. The
        # canonical aggregate is deliberately not given a competing FAILED
        # lifecycle state. Preserve the caller-visible legacy status while
        # keeping actual execution authority in OperationalExecution.
        self._canonical(execution)
        execution.status = ExecutionStatus.FAILED
        return execution
