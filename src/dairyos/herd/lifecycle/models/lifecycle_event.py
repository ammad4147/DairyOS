from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class LifecycleEvent:
    """
    Domain event representing an animal lifecycle transition.

    Lifecycle rules are owned by:
        LifecycleEngine

    Downstream operational projections consume
    the published event.

    Every event receives its own timestamp.
    """

    animal_id: str

    previous_status: str

    new_status: str

    location: str

    event_type: str

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )