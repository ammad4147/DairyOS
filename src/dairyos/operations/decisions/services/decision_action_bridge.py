from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)


class DecisionActionBridge:
    """
    Converts operational decisions into executable farm work.

    Flow:

    OperationalDecision
            |
            v
    OperationalAction
            |
            v
    OperationalExecution

    Traceability:

    Decision ID
        |
        v
    OperationalAction.source_decision_id
        |
        v
    OperationalExecution.action_id


    This bridge does not:
    - complete work
    - verify execution
    - mutate Farm Operational State
    """


    def __init__(
        self,
        action_service: OperationalActionService,
        execution_service: OperationalExecutionService,
    ):

        self.action_service = action_service

        self.execution_service = execution_service


    def create_execution_from_decision(
        self,
        decision,
        assigned_to: str,
        department: str = "Farm Operations",
    ):

        action = self.action_service.create_action(

            title=decision.title,

            description=decision.description,

            assigned_to=assigned_to,

            department=department,

            source_decision_id=decision.decision_id,

            priority=self._map_priority(
                decision.priority.level
            ),

        )


        execution = self.execution_service.create_execution(

            action_id=action.action_id,

            assigned_to=assigned_to,

        )


        return execution


    def _map_priority(
        self,
        priority: str,
    ) -> str:

        mapping = {

            "CRITICAL": "CRITICAL",

            "HIGH": "HIGH",

            "MEDIUM": "NORMAL",

            "LOW": "LOW",

        }


        return mapping.get(

            priority.upper(),

            "NORMAL",

        )
