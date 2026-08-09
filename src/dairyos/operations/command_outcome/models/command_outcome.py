from dataclasses import dataclass
from datetime import datetime

from .outcome_status import OutcomeStatus


@dataclass
class CommandOutcome:
    """
    Records the result of an operational command.
    """

    outcome_id: str
    command_id: str
    impact_score: float
    status: OutcomeStatus
    notes: str
    created_at: datetime
