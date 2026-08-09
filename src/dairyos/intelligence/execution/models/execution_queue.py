from dataclasses import dataclass


@dataclass
class ExecutionQueue:
    """
    Represents an execution queue.
    """

    workflow_type: str

    queue_name: str

    pending_tasks: int

    status: str
