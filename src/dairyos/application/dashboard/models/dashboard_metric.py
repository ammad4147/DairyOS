from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardMetric:
    """
    Generic dashboard metric.
    """

    name: str
    value: float
    unit: str
    status: str = "normal"
