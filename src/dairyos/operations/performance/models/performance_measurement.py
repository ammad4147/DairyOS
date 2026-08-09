from dataclasses import dataclass


@dataclass
class PerformanceMeasurement:
    """
    Records actual operational performance.
    """

    measurement_id: str
    kpi_id: str
    actual_value: float
    period: str
