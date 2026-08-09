from dairyos.operations.workforce_intelligence.models.workforce_accountability_snapshot import (
    WorkforceAccountabilitySnapshot,
)


class WorkforceAccountabilityService:
    """
    Generates workforce accountability intelligence.
    """


    def __init__(
        self,
        execution_repository,
        accountability_repository,
    ):

        self.execution_repository = (
            execution_repository
        )

        self.accountability_repository = (
            accountability_repository
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
                if metric.execution_status == "completed"
            ]
        )


        pending_tasks = (
            total_tasks
            -
            completed_tasks
        )


        overdue_tasks = len(
            [
                metric
                for metric in metrics
                if metric.execution_status == "overdue"
            ]
        )


        if total_tasks == 0:

            accountability_score = 100.0

        else:

            accountability_score = (
                completed_tasks
                /
                total_tasks
                *
                100
            )


        if overdue_tasks > 0:

            accountability_status = "CRITICAL"

        elif accountability_score >= 90:

            accountability_status = "HIGH"

        elif accountability_score >= 70:

            accountability_status = "MEDIUM"

        else:

            accountability_status = "LOW"



        snapshot = WorkforceAccountabilitySnapshot(

            total_tasks=total_tasks,

            completed_tasks=completed_tasks,

            pending_tasks=pending_tasks,

            overdue_tasks=overdue_tasks,

            accountability_score=round(
                accountability_score,
                2,
            ),

            accountability_status=accountability_status,

            escalation_required=(
                accountability_status
                in
                [
                    "CRITICAL",
                    "LOW",
                ]
            ),

        )


        return (
            self.accountability_repository.save(
                snapshot
            )
        )


    def generate_summary(
        self,
    ):
        """
        Command-level compatibility method.

        WorkforceCommandService consumes
        workforce intelligence through
        generate_summary().
        """

        return self.generate_snapshot()
