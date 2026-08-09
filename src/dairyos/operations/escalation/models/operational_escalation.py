from dataclasses import dataclass
from datetime import datetime

from .escalation_level import EscalationLevel


@dataclass
class OperationalEscalation:
    """
    Represents an escalated operational issue.
    """

    escalation_id: str
    issue_reference: str
    level: EscalationLevel
    assigned_to: str
    created_at: datetime
    resolved: bool = False
