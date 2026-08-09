from dataclasses import dataclass



@dataclass
class DecisionMemory:


    decision_id: str

    category: str

    decision: str

    reason: str

    priority: str

    owner: str

    status: str

    outcome: str
