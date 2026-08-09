from dataclasses import dataclass



@dataclass
class KnowledgeSummary:


    subject: str

    findings: list[str]

    confidence: float

    explanation: str

