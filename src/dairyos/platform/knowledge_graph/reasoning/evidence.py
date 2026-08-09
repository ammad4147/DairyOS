from dataclasses import dataclass



@dataclass
class Evidence:

    source: str

    relation: str

    confidence: float

