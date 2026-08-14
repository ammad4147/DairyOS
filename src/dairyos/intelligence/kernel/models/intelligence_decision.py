from dataclasses import dataclass, field
from datetime import datetime
from dairyos.core.time_utils import utcnow


@dataclass
class IntelligenceDecision:
    """
    Represents a decision recommendation produced by the intelligence kernel.
    """

    action: str
    rationale: str
    priority: str = "normal"
    timestamp: datetime = field(default_factory=utcnow)