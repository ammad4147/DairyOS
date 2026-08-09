from typing import List

from ..models.operational_scorecard import (
    OperationalScorecard,
)


class ScorecardService:
    """
    Builds operational management scorecards.
    """


    def generate(
        self,
        performance_records: List,
    ) -> OperationalScorecard:


        total = len(performance_records)


        completed = sum(
            1
            for record in performance_records
            if record.completion_status == "COMPLETED"
        )


        pending = total - completed


        if total:

            average_score = (
                sum(
                    record.performance_score
                    for record in performance_records
                )
                / total
            )

        else:

            average_score = 0.0



        if average_score >= 90:

            health = "GREEN"

        elif average_score >= 60:

            health = "AMBER"

        else:

            health = "RED"



        return OperationalScorecard(

            total_tasks=total,

            completed_tasks=completed,

            pending_tasks=pending,

            average_performance_score=average_score,

            operational_health=health,

        )
