from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class OperationalInputReceipt:
    """
    Records receipt of an operational farm input.
    """

    input_type: str

    source: str

    actor: str

    received_at: datetime = (
        datetime.now(UTC)
    )

    payload_summary: dict | None = None
