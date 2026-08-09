from dataclasses import dataclass


@dataclass
class OperationalInputDeviation:

    input_type: str

    expected_frequency: int

    observed_frequency: int

    deviation_detected: bool

    severity: str
