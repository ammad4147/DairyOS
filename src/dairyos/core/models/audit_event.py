"""
Legacy DairyOS AuditEvent compatibility entity.

This module is retained for import compatibility only. It is not a
production SQLAlchemy persistence authority.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AuditEvent:
    id: int | None = None
    action: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
