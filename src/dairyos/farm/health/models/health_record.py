from dataclasses import dataclass
from datetime import datetime, UTC



@dataclass
class HealthRecord:
    """
    Represents an animal health observation.
    """


    record_id: str

    animal_id: str

    observation: str

    severity: str

    recorded_by: str

    recorded_at: datetime = (
        datetime.now(UTC)
    )
