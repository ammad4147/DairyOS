from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class BootstrapState:
    """
    Represents DairyOS platform startup state.
    """

    initialized: bool = False

    started_at: datetime | None = None

    service_count: int = 0

    def mark_started(self, service_count: int):
        self.initialized = True
        self.service_count = service_count
        self.started_at = datetime.now(timezone.utc)
