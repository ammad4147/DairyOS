from dataclasses import dataclass
from datetime import datetime


@dataclass
class IntelligenceDecision:
    """
    Represents a decision recommendation produced by the intelligence kernel.
    """

    action: str
    rationale: str
    priority: str = "normal"
    timestamp: datetime = datetime.utcnow()

