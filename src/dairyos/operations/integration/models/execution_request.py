from dataclasses import dataclass


@dataclass
class ExecutionRequest:
    """
    Request to create an execution
    from an operational action.
    """

    action_id: str

    assigned_to: str
