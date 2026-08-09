from datetime import datetime

from ..models.executive_decision import ExecutiveDecision
from ..models.decision_urgency import DecisionUrgency


class ExecutiveDecisionService:
    """
    Creates executive operational decisions.
    """


    def create_decision(
        self,
        decision_id,
        subject,
        effectiveness_score,
    ):

        if effectiveness_score < 40:

            urgency = DecisionUrgency.CRITICAL
            recommendation = (
                "Immediate corrective management action required"
            )

        elif effectiveness_score < 60:

            urgency = DecisionUrgency.URGENT
            recommendation = (
                "Review and improve operational process"
            )

        elif effectiveness_score < 80:

            urgency = DecisionUrgency.IMPORTANT
            recommendation = (
                "Monitor and optimize performance"
            )

        else:

            urgency = DecisionUrgency.NORMAL
            recommendation = (
                "Maintain current operational practices"
            )


        return ExecutiveDecision(
            decision_id=decision_id,
            subject=subject,
            recommendation=recommendation,
            urgency=urgency,
            created_at=datetime.now(),
        )
