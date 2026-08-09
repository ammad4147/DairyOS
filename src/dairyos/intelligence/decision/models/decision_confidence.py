from dataclasses import dataclass


@dataclass
class DecisionConfidence:
    """
    Represents confidence assessment
    for an intelligence recommendation.

    Future extensions:

    - historical accuracy tracking
    - human feedback scoring
    - model calibration
    """


    recommendation_category: str

    confidence_score: float

    confidence_level: str
