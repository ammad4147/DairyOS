from dataclasses import dataclass


@dataclass
class GovernanceRule:
    rule_id: str
    policy_id: str
    condition: str
    action: str
    enabled: bool = True
