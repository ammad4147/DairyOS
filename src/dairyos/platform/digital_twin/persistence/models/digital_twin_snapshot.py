from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class DigitalTwinSnapshot:

    farm_id: str

    state: dict

    snapshot_type: str

    created_at: datetime = datetime.now(
        timezone.utc
    )

