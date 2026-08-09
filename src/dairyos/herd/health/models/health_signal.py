from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealthSignal:

    animal_id: str

    signal_type: str

    measured_value: str

    expected_value: str

    deviation: str

    severity: str

    source: str

    detected_at: datetime
