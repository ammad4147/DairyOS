from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OperationsDashboard:
    """
    Management summary of operational performance.

    Read-side dashboard model.

    Contains:
        - operational performance metrics
        - milk production command projection
        - operational awareness projections
        - execution intelligence projections

    Does not:
        - mutate farm state
        - create operational facts
    """


    dashboard_id: str

    open_issue_count: int

    resolution_rate: float

    effectiveness_score: float

    created_at: datetime


    daily_milk_production_command_view: dict = field(
        default_factory=dict
    )


    heads_up_notifications: list = field(
        default_factory=list
    )


    task_intelligence: dict = field(
        default_factory=dict
    )


    open_tasks: list = field(
        default_factory=list
    )


    completed_tasks: list = field(
        default_factory=list
    )


    readiness_status: str = "UNKNOWN"


    readiness_risks: list = field(
        default_factory=list
    )


    execution_status: str = "UNKNOWN"


    execution_details: list = field(
        default_factory=list
    )


    @property
    def operational_health(self):

        if self.effectiveness_score >= 80:

            return "GREEN"

        if self.effectiveness_score >= 50:

            return "AMBER"

        return "RED"
