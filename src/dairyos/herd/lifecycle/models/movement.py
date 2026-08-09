from dataclasses import dataclass
from datetime import datetime



@dataclass
class AnimalMovement:

    animal_id: str

    from_location: str

    to_location: str

    reason: str

    timestamp: datetime = datetime.utcnow()
