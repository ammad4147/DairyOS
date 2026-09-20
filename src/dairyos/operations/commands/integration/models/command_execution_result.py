from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class CommandExecutionResult:
    """
    Result returned after operational command execution.
    """

    command_type: str

    status: str

    message: str

    executed_at: datetime = datetime.now(
        UTC
    )
