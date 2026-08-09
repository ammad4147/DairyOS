from dataclasses import dataclass



@dataclass
class DecisionContext:

    subject_type: str

    subject_id: str

    observation: str

    evidence: list[str]

    risk_level: str

