from datetime import datetime, timezone


class WorkflowAlertService:
    """
    Intelligence service for workflow alerts.

    Detects operational risks from workflow
    intelligence projections.
    """


    def __init__(
        self,
        repository,
    ):

        self.repository = repository



    def stalled_workflows(
        self,
    ):

        return [

            workflow

            for workflow in self.repository.all()

            if workflow.status == "started"

            and workflow.completed_at is None

        ]



    def incomplete_workflows(
        self,
    ):

        return [

            workflow

            for workflow in self.repository.all()

            if workflow.status != "completed"

        ]



    def overdue_workflows(
        self,
        threshold_seconds=3600,
    ):

        now = datetime.now(
            timezone.utc
        )


        alerts = []


        for workflow in self.repository.all():

            if workflow.started_at is None:

                continue


            elapsed = (

                now - workflow.started_at

            ).total_seconds()


            if (

                workflow.status != "completed"

                and elapsed > threshold_seconds

            ):

                alerts.append(
                    workflow
                )


        return alerts



    def workload_imbalance(
        self,
    ):

        workload = {}


        for workflow in self.repository.all():

            operator = workflow.assigned_to


            workload[operator] = (
                workload.get(
                    operator,
                    0,
                )
                + 1
            )


        return workload
