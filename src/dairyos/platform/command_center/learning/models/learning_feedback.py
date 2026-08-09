from dataclasses import dataclass



@dataclass
class LearningFeedback:

    source: str

    signal_type: str

    confidence: float

    metadata: dict

