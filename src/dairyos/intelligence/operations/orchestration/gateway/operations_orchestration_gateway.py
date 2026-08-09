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
from dairyos.intelligence.operations.orchestration.services.orchestration_service import (
    OrchestrationService,
)


class OperationsOrchestrationGateway:
    """
    Gateway exposing operations orchestration capabilities
    to higher intelligence layers.

    Future extensions:

    - authorization
    - auditing
    - event publishing
    - external workflow integration
    """

    def __init__(
        self,
        orchestration_service: OrchestrationService | None = None,
    ):
        self._service = (
            orchestration_service
            if orchestration_service
            else OrchestrationService()
        )

    def create_action(
        self,
        action_type: str,
        description: str,
        priority: str,
        source_decision: str,
    ) -> OperationalAction:

        return self._service.create_action(
            action_type=action_type,
            description=description,
            priority=priority,
            source_decision=source_decision,
        )

    def assign_action(
        self,
        action_type: str,
        assigned_to: str,
        assigned_role: str,
    ) -> ActionAssignment:

        return self._service.assign_action(
            action_type=action_type,
            assigned_to=assigned_to,
            assigned_role=assigned_role,
        )

    def record_execution(
        self,
        action_type: str,
        performed_by: str,
        notes: str,
    ) -> ExecutionRecord:

        return self._service.record_execution(
            action_type=action_type,
            performed_by=performed_by,
            notes=notes,
        )

    def record_outcome(
        self,
        action_type: str,
        result: str,
        feedback: str,
        success: bool = True,
    ) -> ActionOutcome:

        return self._service.record_outcome(
            action_type=action_type,
            result=result,
            feedback=feedback,
            success=success,
        )
