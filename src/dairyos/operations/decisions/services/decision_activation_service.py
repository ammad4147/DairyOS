from dairyos.operations.decisions.services.decision_action_bridge import (
    DecisionActionBridge,
)


class DecisionActivationService:
    """
    Activates operational decisions into executable farm work.

    Flow:

    OperationalDecision
            |
            v
    OperationalAction
            |
            v
    OperationalExecution


    Responsibilities:

    - convert decisions requiring action
      into operational work

    Does not:

    - create decisions
    - complete executions
    - mutate operational state
    """


    def __init__(
        self,
        decision_action_bridge: DecisionActionBridge,
    ):

        if decision_action_bridge is None:

            raise ValueError(
                "DecisionActionBridge is required"
            )


        self.decision_action_bridge = (
            decision_action_bridge
        )


    def activate(
        self,
        decision,
        assigned_to: str,
        department: str = "Farm Operations",
    ):

        if decision is None:

            raise ValueError(
                "OperationalDecision is required"
            )


        if not decision.owner_action_required:

            return None


        return (
            self.decision_action_bridge
            .create_execution_from_decision(
                decision=decision,
                assigned_to=assigned_to,
                department=department,
            )
        )
