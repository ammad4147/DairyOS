from dairyos.operations.commands.models.operational_command import (
    OperationalCommand,
)



class CommandDispatcher:
    """
    Executes operational commands.
    """

    def __init__(
        self,
    ):

        self.handlers = {}



    def register(
        self,
        command_type,
        handler,
    ):

        self.handlers[
            command_type
        ] = handler



    def dispatch(
        self,
        command: OperationalCommand,
    ):

        handler = self.handlers.get(
            command.command_type
        )


        if handler is None:

            raise ValueError(
                f"No handler registered for {command.command_type}"
            )


        return handler(command)
