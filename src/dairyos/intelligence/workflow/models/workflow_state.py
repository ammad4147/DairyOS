from dataclasses import dataclass


@dataclass
class WorkflowState:
    """
    Represents workflow lifecycle state.

    Future extensions:

    - transition validation
    - rollback
    - approval checkpoints
    """


    workflow_type: str

    current_state: str

    previous_state: str
