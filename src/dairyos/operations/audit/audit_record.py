from dataclasses import dataclass
from datetime import datetime, timezone



@dataclass
class AuditRecord:


    action: str


    user: str


    timestamp: datetime = datetime.now(timezone.utc)

