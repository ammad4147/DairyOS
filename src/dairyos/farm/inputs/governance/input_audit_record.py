from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class OperationalInputAuditRecord:
    """
    Audit record for operational input governance.
    """

    input_type: str

    actor: str

    source: str

    accepted: bool

    timestamp: datetime = (
        datetime.now(UTC)
    )
