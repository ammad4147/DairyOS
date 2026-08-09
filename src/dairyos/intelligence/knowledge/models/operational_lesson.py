from dataclasses import dataclass


@dataclass
class OperationalLesson:
    """
    Represents learned operational experience.
    """

    source: str

    lesson: str

    impact: str

    confidence: float
