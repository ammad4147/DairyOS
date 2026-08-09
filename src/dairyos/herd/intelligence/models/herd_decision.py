from dataclasses import dataclass



@dataclass
class HerdDecision:


    risk_level: str

    attention_required: bool

    recommendations: list

    priority_level: str = "NORMAL"

    decision_score: int = 0
