from dataclasses import dataclass


@dataclass
class ExecutiveAlert:

    category: str

    priority: str

    severity_score: int

    issue: str

    recommended_action: str