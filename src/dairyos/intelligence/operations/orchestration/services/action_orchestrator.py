from dairyos.intelligence.operations.orchestration.models.operational_action import (
    OperationalAction,
)


class ActionOrchestrator:
    """
    Coordinates creation of operational actions
    from intelligence decisions.

    Future extensions:

    - autonomous triggering
    - approval workflow
    - action prioritization
    """

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
            status="created",
            source_decision=source_decision,
        )
