from dataclasses import dataclass


@dataclass
class GovernanceRule:
    """
    Defines an operational control rule.
    """

    rule_id: str
    title: str
    category: str
    owner_role: str
    frequency: str
    escalation_required: bool
