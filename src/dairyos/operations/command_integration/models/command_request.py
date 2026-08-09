from dataclasses import dataclass
from datetime import datetime

from .command_priority import CommandPriority


@dataclass
class CommandRequest:
    """
    Represents an operational command request.
    """

    command_id: str
    title: str
    instruction: str
    priority: CommandPriority
    created_at: datetime
