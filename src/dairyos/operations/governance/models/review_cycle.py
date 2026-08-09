from dataclasses import dataclass


@dataclass
class ReviewCycle:
    """
    Defines management review frequency.
    """

    cycle_id: str
    name: str
    frequency: str
    responsible_role: str
