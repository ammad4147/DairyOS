from dairyos.farm.command_center.models.command_center_view import (
    CommandCenterView,
)


class CommandCenterProjectionAssembler:
    """
    Converts the operational command center
    into an owner-facing projection.

    No business rules.
    No calculations.
    Only presentation mapping.
    """

    def assemble(
        self,
        *,
        command_center,
    ):
        farm_status = command_center.farm_status

        return CommandCenterView(
            status={
                "milk": farm_status.milk,
                "feeding": farm_status.feeding,
                "breeding": farm_status.breeding,
                "health": farm_status.health,
                "workforce": farm_status.workforce,
                "inventory": farm_status.inventory,
                "equipment": farm_status.equipment,
                "finance": farm_status.finance,
            },
            attention=(
                command_center.notifications
                if command_center.notifications
                else farm_status.attention_queue
            ),
            decisions=command_center.decisions,
            actions=self._actions(command_center.execution),
            confidence={
                "operational_score": command_center.health.get(
                    "operational_score",
                    0,
                ),
                "health_status": command_center.health.get(
                    "health_status",
                ),
            },
        )

    @staticmethod
    def _actions(execution):
        """Extract the operator-facing actions list from `execution`.

        `OperationalCommandCenterService.snapshot()` produces
        `execution={"actions": [...], "count": ..., "open": ...}`; earlier
        code here only accepted a bare list, so the "actions" key was
        silently dropped and the API always reported an empty list even
        when real, actionable items existed. Both shapes are accepted so
        neither current nor future execution producers regress.
        """
        if isinstance(execution, dict):
            actions = execution.get("actions", [])
            return actions if isinstance(actions, list) else []
        if isinstance(execution, list):
            return execution
        return []
