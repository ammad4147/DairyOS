from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class TenantContext:
    """
    Represents a DairyOS tenant boundary.

    A tenant represents an independent farm organization
    operating on the DairyOS platform.
    """

    tenant_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    tenant_name: str = ""

    farm_id: str = ""

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    active: bool = True
