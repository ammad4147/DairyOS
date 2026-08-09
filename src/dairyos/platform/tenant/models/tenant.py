from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Tenant:
    """
    Enterprise tenant definition.

    Represents an isolated DairyOS
    organization or farm environment.
    """

    name: str

    tenant_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    active: bool = True

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )

    def deactivate(self) -> None:
        self.active = False

    def activate(self) -> None:
        self.active = True
