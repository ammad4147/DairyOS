from dataclasses import dataclass



@dataclass
class DecisionLearning:


    action: str

    executions: int

    successes: int

    confidence: int

    recommendation_strength: str
