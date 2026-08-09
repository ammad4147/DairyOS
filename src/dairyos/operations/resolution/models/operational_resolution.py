from dataclasses import dataclass
from datetime import datetime

from .resolution_status import ResolutionStatus


@dataclass
class OperationalResolution:
    """
    Records corrective action for an operational issue.
    """

    resolution_id: str
    issue_reference: str
    action_taken: str
    assigned_to: str
    created_at: datetime
    status: ResolutionStatus = ResolutionStatus.OPEN
