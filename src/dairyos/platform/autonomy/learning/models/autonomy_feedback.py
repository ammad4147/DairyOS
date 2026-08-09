from dataclasses import dataclass



@dataclass
class AutonomyFeedback:

    recommendation_id: str

    outcome: str

    confidence_change: float

