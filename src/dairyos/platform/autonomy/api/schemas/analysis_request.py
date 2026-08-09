from dataclasses import dataclass



@dataclass
class AnalysisRequest:

    problem: str

    evidence: list

    impact: str

    confidence: float

