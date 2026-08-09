from dataclasses import dataclass



@dataclass
class Advisory:


    category: str

    situation: str

    supporting_knowledge: str

    confidence: int

    recommended_action: str
