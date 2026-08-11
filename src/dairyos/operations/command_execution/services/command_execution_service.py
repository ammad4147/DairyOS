from datetime import datetime

from dairyos.operations.execution.services.operational_execution_service import (
    OperationalExecutionService,
)

from ..models.command_execution import CommandExecution
from ..models.execution_status import ExecutionStatus


class CommandExecutionService:
    """
    Compatibility facade for the legacy command-execution API.

    CommandExecution remains a compatibility DTO. Actual operational
    execution is created by the canonical OperationalExecutionService.
    """

    def __init__(self, operational_execution_service=None):
        self.operational_execution_service = (
            operational_execution_service
            or OperationalExecutionService()
        )

    def create_execution(
        self,
        execution_id,
        command_id,
        assigned_to,
    ):
        canonical = self.operational_execution_service.create_execution(
            action_id=command_id,
            assigned_to=assigned_to,
        )

        return CommandExecution(
            execution_id=execution_id,
            command_id=command_id,
            assigned_to=assigned_to,
            status=ExecutionStatus.CREATED,
            created_at=getattr(
                canonical,
                "created_at",
                datetime.now(),
            ),
        )
