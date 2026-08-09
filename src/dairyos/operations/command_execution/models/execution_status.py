from enum import Enum


class ExecutionStatus(Enum):
    """
    Command execution lifecycle.
    """

    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
