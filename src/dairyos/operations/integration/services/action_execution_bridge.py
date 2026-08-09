from dairyos.operations.actions.models.operational_action import (
    OperationalAction,
)

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from dairyos.operations.execution.models.operational_execution import (
    OperationalExecution,
)


class ActionExecutionBridge:
    """
    Converts operational actions
    into executable farm operations.

    Flow:

    OperationalAction
            |
            v
    OperationalExecution


    This bridge does not:
    - complete execution
    - verify execution
    - close execution
    - mutate Farm Operational State
    """


    def __init__(
        self,
        execution_service: OperationalExecutionService,
    ):

        self.execution_service = execution_service


    def create_execution_from_action(
        self,
        action: OperationalAction,
    ) -> OperationalExecution:
        """
        Create farm execution from action.

        Requires:
        - valid action identity
        - assigned operational owner
        """

        if action is None:

            raise ValueError(
                "OperationalAction is required"
            )


        if not action.action_id:

            raise ValueError(
                "OperationalAction requires action_id"
            )


        if (
            action.assignment is None
            or not action.assignment.assigned_to
        ):

            raise ValueError(
                "OperationalAction requires assigned owner"
            )


        return self.execution_service.create_execution(

            action_id=action.action_id,

            assigned_to=(
                action.assignment.assigned_to
            ),

        )
