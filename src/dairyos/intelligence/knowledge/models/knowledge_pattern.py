from dataclasses import dataclass


@dataclass
class KnowledgePattern:
    """
    Represents a discovered operational pattern.
    """

    category: str

    pattern: str

    frequency: int

    confidence: float
