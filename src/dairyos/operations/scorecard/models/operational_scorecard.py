from dataclasses import dataclass


@dataclass
class OperationalScorecard:
    """
    Management view of operational performance.
    """

    total_tasks: int

    completed_tasks: int

    pending_tasks: int

    average_performance_score: float

    operational_health: str
