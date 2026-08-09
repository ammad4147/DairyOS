from dataclasses import dataclass


@dataclass
class PerformanceScorecard:
    """
    Aggregated operational performance view.
    """

    scorecard_id: str
    category: str
    score_percentage: float
