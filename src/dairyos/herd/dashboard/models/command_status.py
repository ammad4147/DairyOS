from dataclasses import dataclass


@dataclass
class CommandStatus:

    status: str

    reason: str

    priority: str
