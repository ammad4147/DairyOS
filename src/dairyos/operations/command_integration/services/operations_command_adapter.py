from datetime import datetime

from ..models.command_request import CommandRequest
from ..models.command_priority import CommandPriority


class OperationsCommandAdapter:
    """
    Converts executive decisions into operational commands.
    """


    def create_command(
        self,
        command_id,
        title,
        decision,
    ):

        if decision.urgency.value == "CRITICAL":

            priority = CommandPriority.CRITICAL

        elif decision.urgency.value == "URGENT":

            priority = CommandPriority.URGENT

        elif decision.urgency.value == "IMPORTANT":

            priority = CommandPriority.IMPORTANT

        else:

            priority = CommandPriority.ROUTINE


        return CommandRequest(
            command_id=command_id,
            title=title,
            instruction=decision.recommendation,
            priority=priority,
            created_at=datetime.now(),
        )
