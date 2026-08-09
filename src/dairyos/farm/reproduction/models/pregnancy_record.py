from dataclasses import dataclass
from datetime import datetime, UTC



@dataclass
class PregnancyRecord:
    """
    Represents pregnancy confirmation.
    """


    pregnancy_id: str

    animal_id: str

    confirmed: bool

    expected_calving_date: str

    checked_by: str

    checked_at: datetime = (
        datetime.now(UTC)
    )
