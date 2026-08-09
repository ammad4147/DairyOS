from dataclasses import dataclass
from datetime import datetime

from .decision_urgency import DecisionUrgency


@dataclass
class ExecutiveDecision:
    """
    Represents an operational management decision.
    """

    decision_id: str
    subject: str
    recommendation: str
    urgency: DecisionUrgency
    created_at: datetime
