from dataclasses import dataclass


@dataclass
class ExecutionTask:
    """
    Represents a single executable task.
    """

    workflow_type: str

    task_name: str

    assigned_to: str

    status: str
