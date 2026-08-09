from ..models.executive_operations_summary import (
    ExecutiveOperationsSummary,
)


class OperationsCommandBridge:
    """
    Converts executive operations information
    into Farm Command Center compatible signals.
    """

    def translate(
        self,
        summary: ExecutiveOperationsSummary,
    ) -> dict:

        return {
            "domain": "OPERATIONS",
            "health_status": summary.health_status,
            "risk_level": self._risk_level(
                summary.health_status
            ),
            "owner_action_required": (
                summary.owner_action_required
            ),
            "recommended_focus": (
                summary.recommended_focus
            ),
            "priority_score": (
                summary.operational_priority_score
            ),
            "critical_items": (
                summary.critical_items
            ),
        }


    def _risk_level(
        self,
        health_status: str,
    ) -> str:

        if health_status == "RED":
            return "HIGH"

        if health_status == "AMBER":
            return "MEDIUM"

        return "LOW"
