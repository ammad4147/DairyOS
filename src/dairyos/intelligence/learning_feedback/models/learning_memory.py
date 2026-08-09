from dataclasses import dataclass


@dataclass
class LearningMemory:
    """
    Represents accumulated intelligence memory.

    Future extensions:

    - pattern recognition
    - knowledge retrieval
    - adaptive recommendations
    """

    category: str

    pattern: str

    frequency: int

    confidence: float
