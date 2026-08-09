from datetime import datetime

from ..models.operations_dashboard import OperationsDashboard


class DashboardBuilderService:
    """
    Builds operations dashboard snapshots.

    Read-side projection builder.

    Does not:
        - create operational facts
        - mutate farm state
    """


    def build(
        self,
        dashboard_id,
        open_issue_count,
        resolution_rate,
        effectiveness_score,
        daily_milk_production_command_view=None,
        heads_up_notifications=None,
        task_intelligence=None,
        open_tasks=None,
        completed_tasks=None,
        readiness_status="UNKNOWN",
        readiness_risks=None,
        execution_status="UNKNOWN",
        execution_details=None,
    ):

        return OperationsDashboard(

            dashboard_id=dashboard_id,

            open_issue_count=open_issue_count,

            resolution_rate=resolution_rate,

            effectiveness_score=effectiveness_score,

            created_at=datetime.now(),


            daily_milk_production_command_view=(
                daily_milk_production_command_view
                if daily_milk_production_command_view is not None
                else {}
            ),


            heads_up_notifications=(
                heads_up_notifications
                if heads_up_notifications is not None
                else []
            ),


            task_intelligence=(
                task_intelligence
                if task_intelligence is not None
                else {}
            ),


            open_tasks=(
                open_tasks
                if open_tasks is not None
                else []
            ),


            completed_tasks=(
                completed_tasks
                if completed_tasks is not None
                else []
            ),


            readiness_status=readiness_status,


            readiness_risks=(
                readiness_risks
                if readiness_risks is not None
                else []
            ),


            execution_status=execution_status,


            execution_details=(
                execution_details
                if execution_details is not None
                else []
            ),
        )
