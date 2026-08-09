from dataclasses import dataclass



@dataclass
class DecisionPriority:

    title: str

    score: float

    recommended_action: str

    department: str

