
from ..models.operational_decision import OperationalDecision


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
        decisions: list[OperationalDecision],
    ) -> list[OperationalDecision]:

        return sorted(
            decisions,
            key=lambda item: item.priority.score,
            reverse=True,
        )

