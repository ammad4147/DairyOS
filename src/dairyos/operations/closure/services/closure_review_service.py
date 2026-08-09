from ..models.closure_status import ClosureStatus


class ClosureReviewService:
    """
    Reviews effectiveness of corrective actions.
    """


    def review(
        self,
        closure,
    ):

        if closure.effectiveness_score >= 80:

            closure.status = ClosureStatus.ACCEPTED

        else:

            closure.status = ClosureStatus.REVIEW


        return closure
