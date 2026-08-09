from dataclasses import dataclass


@dataclass
class KnowledgeRule:
    """
    Represents an actionable intelligence rule.
    """

    domain: str

    condition: str

    action: str

    confidence: float
