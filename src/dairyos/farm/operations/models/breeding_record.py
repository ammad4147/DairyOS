from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class BreedingRecord:
    """
    Animal reproduction event record.

    Represents breeding lifecycle events.

    Used for:

    - heat detection
    - insemination tracking
    - pregnancy monitoring
    """

    animal_id: str

    event_type: str

    result: str

    technician: str

    record_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
