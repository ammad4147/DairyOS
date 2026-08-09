from typing import List

from ..models.operational_decision import OperationalDecision
from ..models.decision_priority import DecisionPriority


class DecisionRankingService:
    """
    Ranks operational decisions by business urgency.
    """

    PRIORITY_SCORE = {
        "CRITICAL": 100,
        "HIGH": 75,
        "MEDIUM": 50,
        "LOW": 25,
    }

    def rank(
        self,
        decisions: List[OperationalDecision],
    ) -> List[OperationalDecision]:

        return sorted(
            decisions,
            key=lambda item: item.priority.score,
            reverse=True,
        )

