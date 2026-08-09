from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """
    Represents the outcome of execution.

    Future extensions:

    - KPI measurements
    - evidence
    - audit trail
    """

    workflow_type: str

    success: bool

    result: str

    feedback: str
