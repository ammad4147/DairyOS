from dataclasses import dataclass
from datetime import datetime

from .execution_status import ExecutionStatus


@dataclass
class CommandExecution:
    """
    Legacy command-dispatch compatibility DTO.

    CommandExecution is not an execution aggregate and does not own the
    operational execution lifecycle. The authoritative aggregate is
    ``dairyos.operations.execution.models.OperationalExecution``.

    ``status`` is retained only as a legacy command-facing projection.
    Actual lifecycle transitions are performed on the canonical aggregate.
    """

    execution_id: str
    command_id: str
    assigned_to: str
    status: ExecutionStatus
    created_at: datetime

    @property
    def canonical_execution(self):
        """Return the authoritative OperationalExecution, when attached."""
        return getattr(self, "_canonical_execution", None)
