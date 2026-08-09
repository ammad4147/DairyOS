from dataclasses import dataclass


@dataclass
class ExecutionPlan:
    """
    Represents an execution plan generated
    from a workflow.

    Future extensions:

    - scheduling
    - optimization
    - dependencies
    """

    workflow_type: str

    objective: str

    priority: str

    status: str
