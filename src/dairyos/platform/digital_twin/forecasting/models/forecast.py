from dataclasses import dataclass



@dataclass
class Forecast:

    metric: str

    current_value: float

    predicted_value: float

    horizon_days: int

    confidence: float

