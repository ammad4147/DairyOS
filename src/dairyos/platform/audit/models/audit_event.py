from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class AuditEvent:
    """
    Enterprise audit record.

    Represents a traceable system activity.
    """

    event_id: str
    user_id: str
    tenant_id: str
    action: str
    resource: str
    outcome: str
    timestamp: datetime = datetime.now(timezone.utc)

    def is_successful(self) -> bool:
        return self.outcome.upper() == "SUCCESS"
