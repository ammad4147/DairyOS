from dataclasses import dataclass, field


@dataclass
class MilkHealthSummary:
    """
    Read model representing milk-related intelligence
    available to the farm command center.

    This is a dashboard contract only.
    It does not replace milk or health domains.
    """

    milk_anomalies: int = 0

    milk_health_risks: int = 0

    recommended_checks: list[str] = field(
        default_factory=list
    )
