from dataclasses import dataclass
from datetime import datetime, UTC



@dataclass
class HeatEvent:
    """
    Represents heat detection.
    """


    event_id: str

    animal_id: str

    heat_detected: bool

    detected_by: str

    detected_at: datetime = (
        datetime.now(UTC)
    )
