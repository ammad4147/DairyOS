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


class OperationsOrchestrationService:
    """
    Coordinates operational intelligence execution flow.

    Converts intelligence decisions into
    trackable operational activities.

    Future extensions:

    - autonomous dispatching
    - approval workflows
    - execution monitoring
    - learning feedback integration
    """


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

        return ExecutionRecord(
            action_type=action.action_type,
            performed_by=performed_by,
            execution_status="completed",
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
