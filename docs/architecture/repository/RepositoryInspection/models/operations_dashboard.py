from dataclasses import dataclass
from datetime import datetime


@dataclass
class OperationsDashboard:
    """
    Management summary of operational performance.
    """

    dashboard_id: str
    open_issue_count: int
    resolution_rate: float
    effectiveness_score: float
    created_at: datetime


    @property
    def operational_health(self):

        if self.effectiveness_score >= 80:

            return "GREEN"

        if self.effectiveness_score >= 50:

            return "AMBER"

        return "RED"
