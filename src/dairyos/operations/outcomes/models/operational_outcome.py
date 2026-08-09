from dataclasses import dataclass, field
from datetime import datetime

from .outcome_rating import OutcomeRating
from .outcome_feedback import OutcomeFeedback


@dataclass
class OperationalOutcome:
    """
    Result produced after operational action execution.
    """

    outcome_id: str
    action_id: str
    result: str
    rating: OutcomeRating
    feedback: OutcomeFeedback
    created_at: datetime = field(default_factory=datetime.now)

