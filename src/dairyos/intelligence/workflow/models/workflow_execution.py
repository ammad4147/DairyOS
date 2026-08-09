from dataclasses import dataclass


@dataclass
class WorkflowExecution:
    """
    Represents workflow execution tracking.

    Future extensions:

    - timestamps
    - execution duration
    - retry count
    """


    workflow_type: str

    execution_status: str

    executed_by: str

    notes: str
