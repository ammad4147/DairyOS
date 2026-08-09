from enum import Enum


class CommandPriority(Enum):
    """
    Operational command priority.
    """

    ROUTINE = "ROUTINE"
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"
