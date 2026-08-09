from dataclasses import dataclass



@dataclass
class DigitalTwinSignal:

    source: str

    metric: str

    severity: str

    message: str

    confidence: float

