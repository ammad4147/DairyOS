from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)


class ScheduleExecutionBridge:
    """
    Converts scheduled farm shifts
    into executable operational work.
    """


    def __init__(
        self,
        action_service: OperationalActionService,
        execution_service: OperationalExecutionService,
    ):

        self.action_service = action_service

        self.execution_service = execution_service


    def create_execution_from_shift(
        self,
        shift,
    ):

        action = self.action_service.create_action(
            title=shift.name,
            description=(
                f"Scheduled task: {shift.task_category}"
            ),
            assigned_to=shift.assigned_role,
            department="Farm Operations",
        )


        execution = self.execution_service.create_execution(
            action_id=action.action_id,
            assigned_to=shift.assigned_role,
        )


        return execution
