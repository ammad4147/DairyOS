from dataclasses import dataclass



@dataclass
class PredictiveSignal:


    category: str

    pattern: str

    risk: str

    confidence: int

    recommended_action: str
