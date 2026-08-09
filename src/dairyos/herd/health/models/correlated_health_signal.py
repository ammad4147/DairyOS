from dataclasses import dataclass
from datetime import datetime


@dataclass
class CorrelatedHealthSignal:

    animal_id: str

    signals: list

    risk_level: str

    reasons: list

    recommended_checks: list

    detected_at: datetime
