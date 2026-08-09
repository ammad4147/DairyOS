from datetime import datetime

from ..models.command_execution import CommandExecution
from ..models.execution_status import ExecutionStatus


class CommandExecutionService:
    """
    Creates command executions.
    """


    def create_execution(
        self,
        execution_id,
        command_id,
        assigned_to,
    ):

        return CommandExecution(
            execution_id=execution_id,
            command_id=command_id,
            assigned_to=assigned_to,
            status=ExecutionStatus.CREATED,
            created_at=datetime.now(),
        )
