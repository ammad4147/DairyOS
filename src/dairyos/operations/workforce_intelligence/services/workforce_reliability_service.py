from dairyos.operations.workforce_intelligence.models.workforce_reliability_snapshot import (
    WorkforceReliabilitySnapshot,
)


class WorkforceReliabilityService:
    """
    Generates workforce reliability intelligence.

    Uses measured execution history only.
    """


    def __init__(
        self,
        execution_repository,
        reliability_repository,
    ):

        self.execution_repository = (
            execution_repository
        )

        self.reliability_repository = (
            reliability_repository
        )



    def generate_snapshot(
        self,
    ):

        metrics = (
            self.execution_repository.all()
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



        snapshot = WorkforceReliabilitySnapshot(

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

            reliability_status=(
                reliability_status
            ),

            attention_required=(
                reliability_status
                !=
                "HIGH"
            ),

        )


        return (
            self.reliability_repository.save(
                snapshot
            )
        )



    def generate_summary(
        self,
    ):

        return self.generate_snapshot()