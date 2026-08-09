from dataclasses import dataclass



@dataclass
class Recommendation:

    title: str

    action: str

    reason: str

    expected_outcome: str

    confidence: float

    priority: str

    status: str = "new"

