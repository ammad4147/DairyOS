from dataclasses import dataclass



@dataclass
class IntelligentAlert:


    category: str

    issue: str

    severity: str

    urgency: str

    priority_score: int

    recommended_action: str
