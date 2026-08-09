from dataclasses import dataclass



@dataclass
class OutcomeEvaluation:

    expected_result: str

    actual_result: str

    success_score: float

