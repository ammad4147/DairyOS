from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PlatformRuntimeState:
    """
    Represents current enterprise platform runtime state.
    """

    runtime_id: str
    active: bool = True
    started_at: datetime = datetime.now(timezone.utc)

    def is_running(self) -> bool:
        return self.active
