from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class PlatformRuntimeState:
    """
    Represents current enterprise platform runtime state.
    """

    runtime_id: str
    active: bool = True
    started_at: datetime = datetime.now(UTC)

    def is_running(self) -> bool:
        return self.active
