from dairyos.operations.commands.models.operational_command import (
    OperationalCommand,
)



class MilkProductionCommand(
    OperationalCommand
):
    """
    Command issued when milk production
    is recorded.
    """


    def __init__(
        self,
        actor: str,
        cow_id: str,
        litres: float,
    ):

        super().__init__(

            command_type="milk_production_recorded",

            actor=actor,

            payload={

                "cow_id": cow_id,

                "litres": litres,

            },

        )
