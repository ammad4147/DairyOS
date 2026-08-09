from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



@dataclass
class OperationalEvent:


    event_id: str = field(

        default_factory=lambda: str(uuid4())

    )


    event_type: str = ""


    farm_id: str = ""


    entity_id: str = ""


    performed_by: str = ""


    status: str = "recorded"


    timestamp: datetime = field(

        default_factory=lambda:

            datetime.now(timezone.utc)

    )

