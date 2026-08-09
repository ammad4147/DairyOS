from dataclasses import dataclass, field


@dataclass(frozen=True)
class OperationalStateReadModel:
    """
    Immutable dashboard-safe representation
    of current farm operational state.

    Query-side model only.

    Represents the complete operational projection
    exposed from FarmOperationalState.

    Does not contain:
        - business rules
        - mutation methods
        - event processing
        - persistence logic
    """

    farm_id: str

    operational_date: str


    # Core operational domains

    milk_status: dict

    feeding_status: dict

    breeding_status: dict = field(
        default_factory=dict
    )

    workforce_status: dict = field(
        default_factory=dict
    )

    inventory_status: dict = field(
        default_factory=dict
    )

    equipment_status: dict = field(
        default_factory=dict
    )


    # Health and exception awareness

    health_alerts: list = field(
        default_factory=list
    )

    health_alert_count: int = 0

    exception_count: int = 0

    exceptions: list = field(
        default_factory=list
    )


    # Operational freshness

    operational_freshness: dict = field(
        default_factory=dict
    )


    # Production summary

    milk_production_summary: dict = field(
        default_factory=dict
    )

    milk_total: float = 0

    feed_total: float = 0


    # Scheduling state

    schedule_state: dict = field(
        default_factory=dict
    )


    # Task lifecycle

    open_tasks: list = field(
        default_factory=list
    )

    completed_tasks: list = field(
        default_factory=list
    )

    open_task_count: int = 0

    completed_task_count: int = 0


    # Heads-up operational communication

    heads_up_notifications: list = field(
        default_factory=list
    )

    heads_up_count: int = 0


    # Status projections

    health_status: str = "UNKNOWN"

    operational_status: str = "UNKNOWN"


    readiness_status: str = "UNKNOWN"


    readiness_risks: list = field(
        default_factory=list
    )


    # Intelligence projections

    milk_production_intelligence: dict = field(
        default_factory=dict
    )

    milk_production_analytics: dict = field(
        default_factory=dict
    )

    milk_production_trend_intelligence: dict = field(
        default_factory=dict
    )

    daily_milk_production_command_view: dict = field(
        default_factory=dict
    )


    # Task and execution intelligence

    task_intelligence: dict = field(
        default_factory=dict
    )

    execution_tracking: dict = field(
        default_factory=dict
    )

    execution_history_compliance: dict = field(
        default_factory=dict
    )


    execution_total_activities: int = 0

    execution_completed_activities: int = 0

    execution_missed_activities: int = 0


    execution_status: str = "UNKNOWN"


    execution_details: list = field(
        default_factory=list
    )
