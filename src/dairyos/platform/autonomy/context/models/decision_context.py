from dataclasses import dataclass



@dataclass
class DecisionContext:

    problem: str

    evidence: list

    impact: str

    confidence: float

