from dairyos.operations.workforce_intelligence.models.workforce_ownership_snapshot import (
    WorkforceOwnershipSnapshot,
)


class WorkforceOwnershipService:
    """
    Generates workforce ownership intelligence.
    """


    def __init__(
        self,
        execution_repository,
        ownership_repository,
    ):

        self.execution_repository = (
            execution_repository
        )

        self.ownership_repository = (
            ownership_repository
        )


    def generate_snapshot(
        self,
    ):

        metrics = (
            self.execution_repository.all()
        )


        total_responsibilities = len(
            metrics
        )


        completed_responsibilities = len(
            [
                metric
                for metric in metrics
                if metric.execution_status == "completed"
            ]
        )


        pending_responsibilities = (
            total_responsibilities
            -
            completed_responsibilities
        )


        if total_responsibilities == 0:

            ownership_score = 100.0

        else:

            ownership_score = (
                completed_responsibilities
                /
                total_responsibilities
                *
                100
            )


        if ownership_score >= 90:

            ownership_status = "HIGH"

        elif ownership_score >= 70:

            ownership_status = "MEDIUM"

        else:

            ownership_status = "LOW"



        snapshot = WorkforceOwnershipSnapshot(

            total_responsibilities=(
                total_responsibilities
            ),

            completed_responsibilities=(
                completed_responsibilities
            ),

            pending_responsibilities=(
                pending_responsibilities
            ),

            ownership_score=round(
                ownership_score,
                2,
            ),

            ownership_status=(
                ownership_status
            ),

            escalation_required=(
                ownership_status == "LOW"
            ),

        )


        return (
            self.ownership_repository.save(
                snapshot
            )
        )


    def generate_summary(
        self,
    ):
        """
        Command compatibility interface.

        Used by WorkforceCommandService.
        """

        return self.generate_snapshot()
