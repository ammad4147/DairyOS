from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class MilkRecord:
    """
    Daily milk production record.

    Supports:

    - farm group milk collection
    - individual animal milk recording

    Used for:

    - production tracking
    - dashboard reporting
    - animal performance analysis
    - operational intelligence
    """

    animal_group: str | None = None

    animal_id: str | None = None

    shift: str = ""

    litres: float = 0.0

    operator: str = ""

    record_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
