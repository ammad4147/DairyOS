class DashboardSummaryService:
    """
    Provides dashboard interpretation.

    Read-side summary only.

    Exposes operational intelligence
    without modifying domain facts.
    """


    def summarize(
        self,
        dashboard,
    ):

        return {

            "health":
                dashboard.operational_health,


            "open_issues":
                dashboard.open_issue_count,


            "resolution_rate":
                dashboard.resolution_rate,


            "effectiveness_score":
                dashboard.effectiveness_score,


            "daily_milk_production_command_view":
                dashboard.daily_milk_production_command_view,


            "heads_up_notifications":
                dashboard.heads_up_notifications,


            "task_intelligence":
                dashboard.task_intelligence,


            "open_tasks":
                dashboard.open_tasks,


            "completed_tasks":
                dashboard.completed_tasks,


            "readiness_status":
                dashboard.readiness_status,


            "readiness_risks":
                dashboard.readiness_risks,


            "execution_status":
                dashboard.execution_status,


            "execution_details":
                dashboard.execution_details,

        }
