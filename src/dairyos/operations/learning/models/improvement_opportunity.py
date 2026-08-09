from dataclasses import dataclass


@dataclass
class ImprovementOpportunity:
    """
    Represents an identified improvement area.
    """

    opportunity_id: str
    title: str
    description: str
    priority: str
    related_pattern_id: str
