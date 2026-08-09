from dataclasses import dataclass


@dataclass
class ComplianceRule:
    rule_id: str
    name: str
    description: str
    severity: str = "medium"
    enabled: bool = True
