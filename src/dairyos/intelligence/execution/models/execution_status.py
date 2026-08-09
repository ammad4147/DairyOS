from dataclasses import dataclass


@dataclass
class ExecutionStatus:
    """
    Represents current execution status.

    Future extensions:

    - progress tracking
    - timeout detection
    - retry management
    """

    workflow_type: str

    current_status: str

    previous_status: str
