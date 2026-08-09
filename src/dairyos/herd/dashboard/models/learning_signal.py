from dataclasses import dataclass



@dataclass
class LearningSignal:


    category: str

    decision: str

    outcome: str

    effectiveness: str

    confidence_adjustment: int

    learning_note: str
