from dataclasses import dataclass


@dataclass
class OperationalInputPattern:

    input_type: str

    expected_frequency: int

    observed_frequency: int

    reliability_score: float
