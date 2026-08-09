from dataclasses import dataclass



@dataclass
class DecisionOptimization:


    condition: str

    selected_action: str

    confidence: float

    reason: str
