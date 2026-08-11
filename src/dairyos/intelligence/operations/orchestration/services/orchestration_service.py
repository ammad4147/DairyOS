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


class OrchestrationService:
    """
    Coordinates operational actions generated from intelligence decisions.

    Action creation and assignment remain orchestration responsibilities.
    Execution is delegated to the canonical OperationalExecution path.
    ExecutionRecord is retained only as a compatibility/result DTO.
    """

    def __init__(self, execution_service=None, tracking_service=None):
        self.execution_service = execution_service or OperationalExecutionService()
        self.tracking_service = tracking_service or ExecutionTrackingService()

    def create_action(
        self,
        action_type: str,
        description: str,
        priority: str,
        source_decision: str,
    ) -> OperationalAction:
        return OperationalAction(
            action_type=action_type,
            description=description,
            priority=priority,
            status="pending",
            source_decision=source_decision,
        )

    def assign_action(
        self,
        action_type: str,
        assigned_to: str,
        assigned_role: str,
    ) -> ActionAssignment:
        return ActionAssignment(
            action_type=action_type,
            assigned_to=assigned_to,
            assigned_role=assigned_role,
            status="assigned",
        )

    def record_execution(
        self,
        action_type: str,
        performed_by: str,
        notes: str,
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
            execution_status=execution.status,
            notes=notes,
        )

    def record_outcome(
        self,
        action_type: str,
        result: str,
        feedback: str,
        success: bool = True,
    ) -> ActionOutcome:
        return ActionOutcome(
            action_type=action_type,
            result=result,
            success=success,
            feedback=feedback,
        )
