from dataclasses import dataclass



@dataclass
class AdaptiveLearning:


    strategy: str

    attempts: int

    successes: int

    success_rate: float

    confidence_adjustment: str
