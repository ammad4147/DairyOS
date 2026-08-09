from dataclasses import dataclass



@dataclass
class Recommendation:

    title: str

    action: str

    confidence: float

    explanation: str

