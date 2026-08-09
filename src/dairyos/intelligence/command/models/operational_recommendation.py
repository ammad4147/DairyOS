from dataclasses import dataclass


@dataclass
class OperationalRecommendation:
    """
    Represents an intelligence generated recommendation.
    """


    recommendation_id: str

    situation_id: str

    action: str

    urgency: str
