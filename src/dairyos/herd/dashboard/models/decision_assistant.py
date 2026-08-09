from dataclasses import dataclass



@dataclass
class DecisionAssistant:


    situation: str

    recommended_action: str

    confidence: int

    priority: str

    reason: str
