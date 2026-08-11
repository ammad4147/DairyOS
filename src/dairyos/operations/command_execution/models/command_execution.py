from dataclasses import dataclass
from datetime import datetime

from .execution_status import ExecutionStatus


@dataclass
class CommandExecution:
    """
    Legacy command-dispatch compatibility DTO.

    CommandExecution does not own operational execution state.
    The canonical execution aggregate is
    ``dairyos.operations.execution.models.OperationalExecution``.

    ``status`` remains available only for backward compatibility with
    command/intelligence callers while lifecycle changes are delegated to
    the canonical execution tracker.
    """

    execution_id: str
    command_id: str
    assigned_to: str
    status: ExecutionStatus
    created_at: datetime
