from dataclasses import dataclass, field


@dataclass
class MilkCommandSnapshot:
    """
    Management snapshot of milk operations.

    Used by DairyOS Command Center
    for owner and manager decisions.
    """


    today_litres: float

    expected_litres: float

    variance_percentage: float

    operational_status: str

    health_alerts: list = field(
        default_factory=list
    )

    attention_items: list = field(
        default_factory=list
    )
