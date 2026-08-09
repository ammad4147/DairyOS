from dataclasses import dataclass


@dataclass
class LearningFeedback:
    """
    Represents feedback captured from execution.

    Future extensions:

    - feedback classification
    - sentiment analysis
    - automated improvement rules
    """

    decision_type: str

    workflow_type: str

    execution_result: str

    success: bool

    feedback: str
