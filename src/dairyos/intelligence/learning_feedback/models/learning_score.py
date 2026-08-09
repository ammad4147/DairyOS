from dataclasses import dataclass


@dataclass
class LearningScore:
    """
    Measures intelligence effectiveness.

    Future extensions:

    - model evaluation
    - decision accuracy tracking
    - optimization metrics
    """

    decision_type: str

    accuracy_score: float

    execution_score: float

    confidence_score: float
