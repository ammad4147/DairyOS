from dataclasses import dataclass
from datetime import datetime, UTC



@dataclass
class TreatmentRecord:
    """
    Represents treatment administered
    to an animal.
    """


    treatment_id: str

    animal_id: str

    diagnosis: str

    medicine: str

    withdrawal_days: int

    treated_by: str

    treated_at: datetime = (
        datetime.now(UTC)
    )
