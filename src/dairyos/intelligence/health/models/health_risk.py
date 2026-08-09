from dataclasses import dataclass



@dataclass
class HealthRisk:


    animal_id: str

    risk_score: float

    risk_level: str

    recommendation: str
