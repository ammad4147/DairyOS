from ..models.closure_assessment import ClosureAssessment


class ClosureIntelligenceService:
    """
    Evaluates execution outcomes
    and determines closure quality.
    """

    def assess(
        self,
        execution_id: str,
        task_name: str,
        completed: bool,
        performance_score: float,
    ) -> ClosureAssessment:

        if not completed:

            status = "OPEN"

            recommendation = (
                "Execution incomplete. "
                "Follow up required."
            )

        elif performance_score >= 90:

            status = "SUCCESS"

            recommendation = (
                "Operational execution completed "
                "to expected standard."
            )

        elif performance_score >= 60:

            status = "ACCEPTABLE"

            recommendation = (
                "Execution completed but "
                "improvement monitoring required."
            )

        else:

            status = "REVIEW_REQUIRED"

            recommendation = (
                "Operational review required."
            )


        return ClosureAssessment(

            execution_id=execution_id,

            task_name=task_name,

            completed=completed,

            performance_score=performance_score,

            closure_status=status,

            recommendation=recommendation,

        )
