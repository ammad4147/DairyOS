from dataclasses import dataclass


@dataclass
class OwnerAction:

    priority: int

    category: str

    action: str

    urgency: str

    business_impact: str
