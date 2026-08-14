from dataclasses import dataclass, field
from datetime import datetime
from dairyos.core.time_utils import utcnow



@dataclass
class AnimalMovement:

    animal_id: str

    from_location: str

    to_location: str

    reason: str

    timestamp: datetime = field(default_factory=utcnow)