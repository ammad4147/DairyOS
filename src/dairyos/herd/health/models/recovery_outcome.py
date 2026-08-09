from dataclasses import dataclass
from datetime import datetime


@dataclass
class RecoveryOutcome:

    animal_id: str

    outcome: str

    recovery_status: str

    veterinarian: str

    completed_at: datetime
