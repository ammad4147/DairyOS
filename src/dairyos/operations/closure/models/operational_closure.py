from dataclasses import dataclass
from datetime import datetime

from .closure_status import ClosureStatus


@dataclass
class OperationalClosure:
    """
    Records final closure evaluation of an operational issue.
    """

    closure_id: str
    resolution_reference: str
    reviewed_by: str
    effectiveness_score: float
    created_at: datetime
    status: ClosureStatus = ClosureStatus.OPEN
