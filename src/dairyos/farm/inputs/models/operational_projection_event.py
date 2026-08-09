from dataclasses import dataclass
from typing import Any


@dataclass
class OperationalProjectionEvent:

    event_type: str

    payload: dict[str, Any]

    operator: str | None = None