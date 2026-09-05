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

    semen_or_bull: str | None = None

    notes: str | None = None

    semen_lot_id: int | None = None
    semen_supplier: str | None = None
    semen_batch_number: str | None = None
    semen_unit_cost: float | None = None

    record_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
