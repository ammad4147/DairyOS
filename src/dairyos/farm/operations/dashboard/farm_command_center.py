from dataclasses import dataclass, field


@dataclass
class FarmCommandCenter:
    """
    Management projection of current farm operational condition.

    Represents the command center read model.

    Source:
        Farm Operational State
        Intelligence Projection
        Execution Compliance Intelligence

    Responsibilities:
        - expose operational facts
        - expose intelligence signals
        - expose execution compliance visibility
        - support API/dashboard consumption

    Does not:
        - modify farm data
        - execute activities
        - create operational events
    """


    milk_today: float = 0


    feed_quantity_today: float = 0


    feed_cost_today: float = 0


    health_alerts: int = 0


    breeding_pending: int = 0


    operational_status: str = "normal"


    attention_items: list = field(
        default_factory=list
    )


    milk_anomalies: int = 0


    milk_health_risks: int = 0


    milk_recommended_checks: list = field(
        default_factory=list
    )


    open_tasks: list = field(
        default_factory=list
    )


    completed_tasks: list = field(
        default_factory=list
    )


    heads_up_notifications: list = field(
        default_factory=list
    )


    decisions: list = field(
        default_factory=list
    )


    readiness_status: str = "UNKNOWN"


    readiness_risks: list = field(
        default_factory=list
    )


    execution_total_activities: int = 0


    execution_completed_activities: int = 0


    execution_missed_activities: int = 0


    execution_status: str = "UNKNOWN"


    execution_details: list = field(
        default_factory=list
    )


    execution_history_compliance: dict = field(
        default_factory=dict
    )


    # -------------------------------------------------
    # Execution Compliance Intelligence Projection
    # -------------------------------------------------


    execution_scheduled_activities: int = 0


    execution_overdue_activities: int = 0


    execution_compliance_rate: float = 0.0


    execution_risk_level: str = "UNKNOWN"


    execution_attention_required: bool = False
