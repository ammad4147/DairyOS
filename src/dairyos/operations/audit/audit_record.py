from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class AuditRecord:


    action: str


    user: str


    timestamp: datetime = datetime.now(UTC)

