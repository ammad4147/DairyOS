from dairyos.operations.commands.integration.models.command_execution_result import (
    CommandExecutionResult,
)
from dairyos.operations.commands.models.operational_command import (
    OperationalCommand,
)


class OperationalCommandGateway:
    """
    Enterprise boundary for operational command execution.
    """


    def __init__(
        self,
        dispatcher,
    ):

        self.dispatcher = dispatcher



    def execute(
        self,
        command: OperationalCommand,
    ):

        result = self.dispatcher.dispatch(
            command
        )


        return CommandExecutionResult(

            command_type=command.command_type,

            status="completed",

            message=str(result),

        )
