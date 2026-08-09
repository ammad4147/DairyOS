from dataclasses import dataclass


@dataclass
class AutomationRule:
    """
    Defines an operational automation rule.
    """

    rule_id: str
    name: str
    trigger: str
    action: str
    enabled: bool = True
