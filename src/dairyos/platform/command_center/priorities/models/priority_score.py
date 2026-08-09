from dataclasses import dataclass



@dataclass
class PriorityScore:

    score: float

    severity: str

    impact: str

    urgency: str

