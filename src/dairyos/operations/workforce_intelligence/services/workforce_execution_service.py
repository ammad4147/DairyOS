from dairyos.operations.workforce_intelligence.models.execution_metric import (
    ExecutionMetric,
)

from dairyos.operations.workforce_intelligence.models.workforce_execution_snapshot import (
    WorkforceExecutionSnapshot,
)


class WorkforceExecutionService:
    """
    Application service for workforce execution intelligence.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def track_execution(
        self,
        user_id: str,
        action_id: str,
    ):

        metric = ExecutionMetric(

            user_id=user_id,

            action_id=action_id,

        )


        return self.repository.save(
            metric
        )



    def complete_execution(
        self,
        metric_id: str,
    ):

        metric = self.repository.get(
            metric_id
        )


        if metric is None:

            return None


        metric.complete()


        return self.repository.save(
            metric
        )



    def get_user_execution_metrics(
        self,
        user_id: str,
    ):

        return (
            self.repository.by_user(
                user_id
            )
        )



    def get_all_metrics(
        self,
    ):

        return self.repository.all()



    def generate_snapshot(
        self,
    ):

        metrics = (
            self.get_all_metrics()
        )


        total_assignments = len(
            metrics
        )


        completed_assignments = sum(
            1
            for metric in metrics
            if metric.execution_status == "completed"
        )


        pending_assignments = (
            total_assignments
            -
            completed_assignments
        )


        if total_assignments:

            completion_rate = (
                completed_assignments
                /
                total_assignments
            )

        else:

            completion_rate = 1.0



        if completion_rate >= 0.90:

            execution_health = "GREEN"

            attention_required = False


        elif completion_rate >= 0.75:

            execution_health = "AMBER"

            attention_required = True


        else:

            execution_health = "RED"

            attention_required = True



        return WorkforceExecutionSnapshot(

            total_assignments=(
                total_assignments
            ),

            completed_assignments=(
                completed_assignments
            ),

            pending_assignments=(
                pending_assignments
            ),

            completion_rate=(
                completion_rate
            ),

            execution_health=(
                execution_health
            ),

            attention_required=(
                attention_required
            ),

        )