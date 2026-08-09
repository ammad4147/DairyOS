from dataclasses import dataclass



@dataclass
class GovernanceRule:

    """
    Enterprise governance validation rule.
    """

    key: str

    description: str

    enabled: bool = True
