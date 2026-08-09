from dairyos.farm.command_center.models.operational_command_center import (
    OperationalCommandCenter,
)

from dairyos.farm.command_center.models.farm_status_snapshot import (
    FarmStatusSnapshot,
)


class OperationalCommandCenterAssembler:
    """
    Composes the unified operational view.

    No business logic belongs here.

    The assembler only maps existing operational
    state into Command Center presentation models.
    """

    def assemble(
        self,
        *,
        farm_state,
        health,
        dashboard,
        notifications,
        decisions,
        execution,
        intelligence,
    ):

        farm_status = FarmStatusSnapshot(

            milk=farm_state.get(
                "milk",
                {},
            ),

            feeding=farm_state.get(
                "feeding",
                {},
            ),

            breeding=farm_state.get(
                "breeding",
                {},
            ),

            health=farm_state.get(
                "health",
                {},
            ),

            inventory=farm_state.get(
                "inventory",
                {},
            ),

            equipment=farm_state.get(
                "equipment",
                {},
            ),

            workforce=farm_state.get(
                "workforce",
                {},
            ),

            finance=farm_state.get(
                "finance",
                {},
            ),

            attention_queue=farm_state.get(
                "attention_queue",
                [],
            ),
        )


        return OperationalCommandCenter(

            farm_status=farm_status,

            health=health,

            dashboard=dashboard,

            notifications=notifications,

            decisions=decisions,

            execution=execution,

            intelligence=intelligence,

        )
