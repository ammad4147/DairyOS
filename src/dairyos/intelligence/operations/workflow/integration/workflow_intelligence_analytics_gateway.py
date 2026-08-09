class WorkflowIntelligenceAnalyticsGateway:
    """
    Integration boundary for workflow analytics.

    Provides dashboard-safe operational metrics.
    """


    def __init__(
        self,
        analytics_service,
    ):

        self.analytics_service = analytics_service



    def get_total_workflows(
        self,
    ):

        return self.analytics_service.total_workflows()



    def get_completed_workflows(
        self,
    ):

        return self.analytics_service.completed_count()



    def get_active_workflows(
        self,
    ):

        return self.analytics_service.active_count()



    def get_average_completion_duration_seconds(
        self,
    ):

        return (
            self.analytics_service
            .average_completion_duration_seconds()
        )



    def get_operator_workload(
        self,
    ):

        return self.analytics_service.workload_by_operator()
