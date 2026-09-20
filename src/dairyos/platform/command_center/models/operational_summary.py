from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class OperationalSummary:

    domain: str

    status: str

    metrics: dict

    generated_at: datetime = datetime.now(UTC)

