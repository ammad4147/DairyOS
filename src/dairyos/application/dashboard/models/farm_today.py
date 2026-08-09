from dataclasses import dataclass, field
from datetime import date

from .dashboard_alert import DashboardAlert
from .dashboard_metric import DashboardMetric
from .dashboard_activity import DashboardActivity
from .dashboard_action import DashboardAction

from .milk_command import MilkCommand
from .herd_command import HerdCommand
from .breeding_command import BreedingCommand
from .financial_command import FinancialCommand



@dataclass
class FarmTodaySnapshot:
    """
    Daily operational dashboard snapshot.

    Read model only.

    Domain ownership remains
    inside operational modules.

    Capability-2 command foundation:
        - Milk command
        - Herd command
        - Breeding command
        - Financial command
    """


    snapshot_date: date


    total_animals: int = 0

    milking_animals: int = 0

    dry_animals: int = 0


    milk_total_litres: float = 0.0

    feed_consumption_kg: float = 0.0


    completed_tasks: int = 0

    pending_tasks: int = 0

    overdue_tasks: int = 0


    milk_command: MilkCommand = field(
        default_factory=MilkCommand
    )


    herd_command: HerdCommand = field(
        default_factory=HerdCommand
    )


    breeding_command: BreedingCommand = field(
        default_factory=BreedingCommand
    )


    financial_command: FinancialCommand = field(
        default_factory=FinancialCommand
    )


    daily_milk_production_command_view: dict = field(
        default_factory=dict
    )


    metrics: list[DashboardMetric] = field(
        default_factory=list
    )


    alerts: list[DashboardAlert] = field(
        default_factory=list
    )


    activities: list[DashboardActivity] = field(
        default_factory=list
    )


    actions: list[DashboardAction] = field(
        default_factory=list
    )


    operational_events: list = field(
        default_factory=list
    )
