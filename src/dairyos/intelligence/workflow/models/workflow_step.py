from dataclasses import dataclass


@dataclass
class WorkflowStep:
    """
    Represents a workflow step.

    Future extensions:

    - conditional branching
    - retry policies
    - timeout handling
    """


    workflow_type: str

    step_name: str

    sequence: int

    status: str
