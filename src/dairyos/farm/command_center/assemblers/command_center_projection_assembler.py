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

                "milk":
                    farm_status.milk,

                "feeding":
                    farm_status.feeding,

                "breeding":
                    farm_status.breeding,

                "health":
                    farm_status.health,

                "workforce":
                    farm_status.workforce,

                "inventory":
                    farm_status.inventory,

                "equipment":
                    farm_status.equipment,

                "finance":
                    farm_status.finance,

            },


            attention=(
                command_center.notifications
            ),


            decisions=(
                command_center.decisions
            ),


            actions=(
                command_center.execution
                if isinstance(
                    command_center.execution,
                    list,
                )
                else []
            ),


            confidence={

                "operational_score":
                    command_center.health.get(
                        "operational_score",
                        0,
                    ),

                "health_status":
                    command_center.health.get(
                        "health_status",
                    ),

            },

        )
