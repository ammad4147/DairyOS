from dataclasses import dataclass
from typing import Any


@dataclass
class OperationalProjectionEvent:

    event_type: str

    payload: dict[str, Any]

    operator: str | None = None
    event_id: str | None = None
    timestamp: object = None
