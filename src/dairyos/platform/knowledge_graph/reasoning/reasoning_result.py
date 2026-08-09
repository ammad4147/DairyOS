from dataclasses import dataclass



@dataclass
class ReasoningResult:

    observation: str

    conclusion: str

    confidence: float

    evidence_count: int

