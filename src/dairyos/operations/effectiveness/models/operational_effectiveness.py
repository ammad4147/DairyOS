from dataclasses import dataclass
from datetime import datetime


@dataclass
class OperationalEffectiveness:
    """
    Represents operational performance evaluation.
    """

    effectiveness_id: str
    operation_reference: str
    response_score: float
    resolution_score: float
    closure_score: float
    created_at: datetime


    @property
    def overall_score(self):

        return (
            self.response_score
            + self.resolution_score
            + self.closure_score
        ) / 3
