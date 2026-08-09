from dataclasses import dataclass


@dataclass
class ExecutionLifecycle:
    """
    Represents current lifecycle position
    of an execution workflow.
    """

    workflow_type: str

    current_state: str

    previous_state: str
