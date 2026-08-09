from typing import List

from ..models.operational_outcome import OperationalOutcome
from ..models.outcome_rating import OutcomeRating
from ..models.outcome_feedback import OutcomeFeedback


class OutcomeRecordService:
    """
    Records operational results.
    """

    def __init__(self):
        self.outcomes: List[OperationalOutcome] = []


    def record_outcome(
        self,
        action_id: str,
        result: str,
        rating: str,
        feedback: OutcomeFeedback,
    ) -> OperationalOutcome:

        outcome = OperationalOutcome(
            outcome_id=f"OUT-{len(self.outcomes)+1:04d}",
            action_id=action_id,
            result=result,
            rating=OutcomeRating(
                rating=rating.upper()
            ),
            feedback=feedback,
        )

        self.outcomes.append(outcome)

        return outcome


    def get_outcomes(self):

        return self.outcomes

