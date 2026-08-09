from dataclasses import dataclass



@dataclass
class AdaptiveRecommendation:


    category: str

    recommended_action: str

    confidence: int

    reason: str
