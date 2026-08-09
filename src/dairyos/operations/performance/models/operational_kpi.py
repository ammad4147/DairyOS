from dataclasses import dataclass


@dataclass
class OperationalKPI:
    """
    Defines an operational performance indicator.
    """

    kpi_id: str
    name: str
    category: str
    target_value: float
    unit: str
