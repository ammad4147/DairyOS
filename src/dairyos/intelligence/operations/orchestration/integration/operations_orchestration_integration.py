from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)

from dairyos.intelligence.operations.orchestration.services.operations_orchestration_service import (
    OperationsOrchestrationService,
)

from dairyos.intelligence.operations.orchestration.repository.adapters.operations_orchestration_repository import (
    OperationsOrchestrationRepository,
)


class OperationsOrchestrationIntegration:
    """
    Integration bridge between intelligence decisions
    and operational execution orchestration.

    Coordinates:

    - action creation
    - assignment generation
    - execution recording
    - outcome tracking

    Future extensions:

    - decision engine adapters
    - event bus integration
    - workflow engines
    - autonomous execution policies
    """


    def __init__(
        self,
        service: OperationsOrchestrationService,
        repository: OperationsOrchestrationRepository,
    ):

        self.service = service

        self.repository = repository



    def process_action(
        self,
        action: OperationalAction,
        assigned_to: str,
        assigned_role: str,
    ):

        self.repository.save_action(action)


        assignment = self.service.create_assignment(
            action,
            assigned_to,
            assigned_role,
        )

        self.repository.save_assignment(
            assignment
        )


        return assignment



    def complete_action(
        self,
        action: OperationalAction,
        performed_by: str,
        notes: str,
        result: str,
        success: bool,
        feedback: str,
    ):

        execution = self.service.record_execution(
            action,
            performed_by,
            notes,
        )

        outcome = self.service.create_outcome(
            action,
            result,
            success,
            feedback,
        )


        self.repository.save_execution(
            execution
        )

        self.repository.save_outcome(
            outcome
        )


        return outcome
