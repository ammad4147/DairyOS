from dataclasses import dataclass



@dataclass
class AutonomyRequest:

    problem: str

    evidence: list

    impact: str

    confidence: float

