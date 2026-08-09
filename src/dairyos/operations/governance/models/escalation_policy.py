from dataclasses import dataclass


@dataclass
class EscalationPolicy:
    """
    Defines escalation behaviour.
    """

    policy_id: str
    issue_category: str
    escalation_level: int
    responsible_role: str
    response_time_hours: int
