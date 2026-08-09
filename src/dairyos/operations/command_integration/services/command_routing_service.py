from ..models.command_priority import CommandPriority


class CommandRoutingService:
    """
    Routes commands requiring attention.
    """


    def requires_immediate_attention(
        self,
        command,
    ):

        return command.priority in [
            CommandPriority.URGENT,
            CommandPriority.CRITICAL,
        ]
