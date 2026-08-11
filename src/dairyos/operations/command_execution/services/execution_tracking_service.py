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

    CommandExecution remains a compatibility DTO only.

    The authoritative lifecycle is always performed against
    dairyos.operations.execution.models.OperationalExecution.
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
            or OperationalExecutionTrackingService()
        )

    def _canonical(self, execution):
        canonical = execution.canonical_execution

        if canonical is not None:
            return canonical

        canonical = self.execution_service.create_execution(
            action_id=execution.command_id,
            assigned_to=execution.assigned_to,
        )

        execution._canonical_execution = canonical

        return canonical

    def start(self, execution):
        """
        Start the canonical operational execution.

        IN_PROGRESS remains only the legacy command-facing projection.
        """
        canonical = self._canonical(execution)

        self.tracking_service.start(
            canonical,
        )

        execution.status = ExecutionStatus.IN_PROGRESS

        return execution

    def complete(self, execution):
        """
        Complete the canonical operational execution.

        COMPLETED on CommandExecution is only a compatibility projection.
        """
        canonical = self._canonical(execution)

        self.tracking_service.complete(
            canonical,
        )

        execution.status = ExecutionStatus.COMPLETED

        return execution

    def failed(self, execution):
        """
        Preserve the legacy failure result without creating a competing
        canonical FAILED execution lifecycle.

        OperationalExecution remains the authoritative execution state.
        Failure is retained here only as a compatibility/outcome value for
        legacy command callers.
        """
        self._canonical(execution)

        execution.status = ExecutionStatus.FAILED

        return execution
