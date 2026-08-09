from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class FarmOperationEvent:
    """
    Base operational event recorded
    during daily farm activities.

    Examples:

    - milk production
    - feeding
    - health observation
    - task completion
    """


    event_type: str

    animal_id: str | None

    operator: str

    payload: dict


    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )


    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
