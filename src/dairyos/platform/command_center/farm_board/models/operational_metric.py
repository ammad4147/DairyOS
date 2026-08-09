from dataclasses import dataclass



@dataclass
class OperationalMetric:

    name: str

    value: float

    unit: str

    trend: str

