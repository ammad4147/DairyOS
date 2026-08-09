from dataclasses import dataclass


@dataclass
class ControlAttention:
    """
    Represents an item requiring management attention.
    """

    attention_id: str
    category: str
    severity: str
    description: str
    recommended_action: str
