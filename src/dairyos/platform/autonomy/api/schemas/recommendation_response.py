from dataclasses import dataclass



@dataclass
class RecommendationResponse:

    recommendation: str

    confidence: float

