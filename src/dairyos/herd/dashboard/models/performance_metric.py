from dataclasses import dataclass


@dataclass
class PerformanceMetric:

    total_actions: int

    completed_actions: int

    open_actions: int

    completion_rate: float

    effectiveness_score: int
