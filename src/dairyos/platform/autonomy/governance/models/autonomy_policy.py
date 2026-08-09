from dataclasses import dataclass



@dataclass
class AutonomyPolicy:

    minimum_confidence: float

    approval_required: bool

    max_risk_level: str

