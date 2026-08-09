from dataclasses import dataclass


@dataclass
class DecisionRecommendation:
    """
    Represents an intelligence-generated recommendation.

    Future extensions:

    - approval workflow
    - decision history
    - human feedback loop
    - outcome tracking
    """


    category: str

    recommendation: str

    rationale: str

    confidence: float

    priority: str
