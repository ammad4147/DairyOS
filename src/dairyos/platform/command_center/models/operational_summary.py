from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class OperationalSummary:

    domain: str

    status: str

    metrics: dict

    generated_at: datetime = datetime.now(timezone.utc)

