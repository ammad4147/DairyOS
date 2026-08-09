from dataclasses import dataclass



@dataclass
class FarmMetric:


    metric_name: str

    value: float

    unit: str

    trend: str

    performance: str
