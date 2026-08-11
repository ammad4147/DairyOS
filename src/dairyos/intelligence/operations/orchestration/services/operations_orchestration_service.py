from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)

from dairyos.intelligence.operations.orchestration.models.action_assignment import (
    ActionAssignment,
)

from dairyos.intelligence.operations.orchestration.models.execution_record import (
    ExecutionRecord,
)

from dairyos.intelligence.operations.orchestration.models.action_outcome import (
    ActionOutcome,
)

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)
from dairyos.operations.execution.services.execution_tracking_service import (
    ExecutionTrackingService,
)


class OperationsOrchestrationService:
    """
    Coordinates operational intelligence flow.

    Decisions, actions, assignments, and outcomes remain orchestration
    concerns. Actual execution lifecycle is delegated to the canonical
    OperationalExecution aggregate.
    """

    def __init__(self, execution_service=None, tracking_service=None):
        self.execution_service = execution_service or OperationalExecutionService()
        self.tracking_service = tracking_service or ExecutionTrackingService()

    def create_assignment(
        self,
        action: OperationalAction,
        assigned_to: str,
        assigned_role: str,
    ) -> ActionAssignment:
        return ActionAssignment(
            action_type=action.action_type,
            assigned_to=assigned_to,
            assigned_role=assigned_role,
            status="assigned",
        )

    def record_execution(
        self,
        action: OperationalAction,
        performed_by: str,
        notes: str,
    ) -> ExecutionRecord:
        execution = self.execution_service.create_execution(
            action_id=action.action_type,
            assigned_to=performed_by,
        )
        self.tracking_service.complete(
            execution,
            notes=notes,
            actor=performed_by,
        )

        return ExecutionRecord(
            action_type=action.action_type,
            performed_by=performed_by,
            execution_status=execution.status.lower(),
            notes=notes,
        )

    def create_outcome(
        self,
        action: OperationalAction,
        result: str,
        success: bool,
        feedback: str,
    ) -> ActionOutcome:
        return ActionOutcome(
            action_type=action.action_type,
            result=result,
            success=success,
            feedback=feedback,
        )
