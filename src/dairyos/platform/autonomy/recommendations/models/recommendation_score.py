from dataclasses import dataclass



@dataclass
class RecommendationScore:

    confidence: float

    impact: str

    urgency: str

