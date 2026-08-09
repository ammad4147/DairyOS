from dairyos.operations.workforce_intelligence.models.workforce_reliability_snapshot import (
    WorkforceReliabilitySnapshot,
)


class WorkforceReliabilitySummaryService:
    """
    Generates workforce reliability summary
    for command center consumption.
    """


    def __init__(
        self,
        execution_repository,
    ):

        self.execution_repository = (
            execution_repository
        )



    def generate_summary(
        self,
    ):

        metrics = (
            self.execution_repository.all()
        )


        total_tasks = len(metrics)


        completed_tasks = len(
            [
                metric
                for metric in metrics
                if metric.execution_status == "completed"
            ]
        )


        pending_tasks = (
            total_tasks - completed_tasks
        )


        if total_tasks == 0:

            completion_rate = 100.0

        else:

            completion_rate = (
                completed_tasks
                /
                total_tasks
                *
                100
            )


        reliability_score = (
            completion_rate
        )


        if reliability_score >= 90:

            reliability_status = "HIGH"

        elif reliability_score >= 70:

            reliability_status = "MEDIUM"

        else:

            reliability_status = "LOW"



        return WorkforceReliabilitySnapshot(

            total_tasks=total_tasks,

            completed_tasks=completed_tasks,

            pending_tasks=pending_tasks,

            completion_rate=round(
                completion_rate,
                2,
            ),

            reliability_score=round(
                reliability_score,
                2,
            ),

            reliability_status=reliability_status,

            attention_required=(
                reliability_status != "HIGH"
            ),

        )