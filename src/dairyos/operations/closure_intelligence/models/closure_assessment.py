from dataclasses import dataclass


@dataclass
class ClosureAssessment:
    """
    Represents operational closure evaluation.
    """

    execution_id: str

    task_name: str

    completed: bool

    performance_score: float

    closure_status: str

    recommendation: str
