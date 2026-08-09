from dataclasses import dataclass


@dataclass
class WorkflowResult:
    """
    Represents workflow completion result.

    Future extensions:

    - KPI tracking
    - audit evidence
    - effectiveness scoring
    """


    workflow_type: str

    success: bool

    result: str

    feedback: str
