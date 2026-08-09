from dairyos.operations.workforce_intelligence.models.workforce_execution_snapshot import (
    WorkforceExecutionSnapshot,
)


class WorkforceExecutionIntelligenceService:
    """
    Converts execution metrics
    into workforce intelligence.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def generate_snapshot(
        self,
    ) -> WorkforceExecutionSnapshot:


        metrics = (
            self.repository.all()
        )


        total = len(metrics)


        completed = len(
            [
                metric
                for metric in metrics
                if metric.execution_status
                == "completed"
            ]
        )


        pending = (
            total - completed
        )


        if total == 0:

            completion_rate = 100.0

        else:

            completion_rate = (
                completed / total
            ) * 100



        if completion_rate >= 90:

            health = "GREEN"

        elif completion_rate >= 70:

            health = "YELLOW"

        else:

            health = "RED"



        return WorkforceExecutionSnapshot(

            total_assignments=total,

            completed_assignments=completed,

            pending_assignments=pending,

            completion_rate=round(
                completion_rate,
                2,
            ),

            execution_health=health,

            attention_required=(
                health != "GREEN"
            ),

        )
