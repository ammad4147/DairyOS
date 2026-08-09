from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class OperationalInputReceipt:
    """
    Records receipt of an operational farm input.
    """

    input_type: str

    source: str

    actor: str

    received_at: datetime = (
        datetime.now(timezone.utc)
    )

    payload_summary: dict | None = None
