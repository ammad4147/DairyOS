from dataclasses import dataclass
from datetime import datetime, UTC



@dataclass
class MilkRecord:
    """
    Represents a milk production entry.

    Created from actual farm milking activity.
    """


    record_id: str

    animal_id: str

    milking_session: str

    litres: float

    recorded_by: str

    recorded_at: datetime = (
        datetime.now(UTC)
    )
