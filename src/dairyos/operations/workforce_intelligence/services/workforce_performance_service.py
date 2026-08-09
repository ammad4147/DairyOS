from dairyos.operations.workforce_intelligence.models.workforce_performance_snapshot import (
    WorkforcePerformanceSnapshot,
)


class WorkforcePerformanceService:
    """
    Generates workforce performance intelligence.
    """


    def __init__(
        self,
        execution_repository,
        performance_repository,
    ):

        self.execution_repository = (
            execution_repository
        )

        self.performance_repository = (
            performance_repository
        )



    def generate_snapshot(
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
                *
                100
            )


        reliability_score = (
            completion_rate
        )


        if reliability_score >= 90:

            performance_status = "GREEN"


        elif reliability_score >= 70:

            performance_status = "YELLOW"


        else:

            performance_status = "RED"



        snapshot = WorkforcePerformanceSnapshot(

            total_tasks=(
                total_tasks
            ),

            completed_tasks=(
                completed_tasks
            ),

            pending_tasks=(
                pending_tasks
            ),

            completion_rate=(
                completion_rate
            ),

            reliability_score=(
                reliability_score
            ),

            performance_status=(
                performance_status
            ),

            attention_required=(
                performance_status != "GREEN"
            ),

        )


        return (
            self.performance_repository.save(
                snapshot
            )
        )



    def generate_summary(
        self,
    ):

        return self.generate_snapshot()