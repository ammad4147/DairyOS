from dataclasses import dataclass


@dataclass
class KnowledgeAdjustment:
    """
    Represents an intelligence improvement.

    Future extensions:

    - automated tuning
    - policy optimization
    - confidence calibration
    """

    decision_area: str

    previous_value: str

    new_value: str

    reason: str
