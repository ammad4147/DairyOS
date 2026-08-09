from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class LearningEvent:
    """
    Represents a learning occurrence.

    Future extensions:

    - event sourcing
    - event correlation
    - distributed learning
    """

    event_type: str

    source: str

    description: str

    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
