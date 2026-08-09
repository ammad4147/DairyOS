from dataclasses import dataclass


@dataclass
class KnowledgePattern:
    """
    Represents a reusable operational learning pattern.
    """

    category: str
    situation: str
    successful_response: str
    confidence: float

