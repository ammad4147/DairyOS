from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass
class HealthObservation:
    """
    Animal health observation record.

    Supports:

    - veterinary observations
    - operational alerts
    - production related health events
    """

    animal_id: str

    observation: str | None = None

    severity: str = "normal"

    reported_by: str | None = None

    observation_type: str | None = None

    notes: str | None = None

    operator: str | None = None

    temperature: float | None = None

    action_taken: str | None = None

    observation_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self):

        if self.observation is None:
            self.observation = self.observation_type

        if self.reported_by is None:
            self.reported_by = self.operator

        if self.action_taken is None:
            self.action_taken = self.notes
