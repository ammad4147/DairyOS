from dairyos.operations.workforce_intelligence.models.workforce_performance_snapshot import (
    WorkforcePerformanceSnapshot,
)


class WorkforcePerformanceSummaryService:
    """
    Generates management workforce performance summaries.

    Converts execution metrics into
    executive workforce intelligence.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def generate_summary(
        self,
    ) -> WorkforcePerformanceSnapshot:


        metrics = (
            self.repository.all()
        )


        total_tasks = len(
            metrics
        )


        completed_tasks = len(
            [
                metric
                for metric in metrics
                if metric.execution_status
                == "completed"
            ]
        )


        pending_tasks = (
            total_tasks
            -
            completed_tasks
        )


        if total_tasks == 0:

            completion_rate = 100.0

        else:

            completion_rate = (
                completed_tasks
                /
                total_tasks
            ) * 100



        reliability_score = (
            completion_rate
        )


        if completion_rate >= 90:

            performance_status = "GREEN"


        elif completion_rate >= 70:

            performance_status = "YELLOW"


        else:

            performance_status = "RED"



        return WorkforcePerformanceSnapshot(

            total_tasks=(
                total_tasks
            ),


            completed_tasks=(
                completed_tasks
            ),


            pending_tasks=(
                pending_tasks
            ),


            completion_rate=round(
                completion_rate,
                2,
            ),


            reliability_score=round(
                reliability_score,
                2,
            ),


            performance_status=(
                performance_status
            ),


            attention_required=(
                performance_status != "GREEN"
            ),

        )
