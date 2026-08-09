from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class ConfigurationChange:

    key: str

    old_value: object

    new_value: object

    changed_by: str

    timestamp: datetime = datetime.now(timezone.utc)
