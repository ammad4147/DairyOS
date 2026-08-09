from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class IntelligenceSignal:
    """
    Represents an operational intelligence observation.

    Signals describe detected conditions.
    They do not change farm operational facts.
    """

    signal_type: str

    severity: str

    source: str

    evidence: dict = field(
        default_factory=dict
    )

    detected_at: datetime = field(
        default_factory=lambda:
        datetime.now(timezone.utc)
    )

    message: str = ""

