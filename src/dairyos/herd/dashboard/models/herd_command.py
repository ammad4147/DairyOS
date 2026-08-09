from dataclasses import dataclass, field



@dataclass
class HerdCommand:


    farm_name: str

    total_animals: int

    production_status: str

    health_status: str

    reproduction_status: str

    financial_status: str

    overall_risk: str

    owner_attention: str

    decision_priority: str = "NORMAL"

    decision_score: int = 0

    recommended_actions: list = field(default_factory=list)
