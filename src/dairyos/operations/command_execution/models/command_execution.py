from dataclasses import dataclass
from datetime import datetime

from .execution_status import ExecutionStatus


@dataclass
class CommandExecution:
    """
    Tracks execution of an operational command.
    """

    execution_id: str
    command_id: str
    assigned_to: str
    status: ExecutionStatus
    created_at: datetime
