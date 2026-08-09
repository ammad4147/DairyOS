class WorkflowIntelligenceAlertGateway:
    """
    Integration boundary for workflow alerts.

    Provides operational risk visibility
    without exposing intelligence internals.
    """


    def __init__(
        self,
        alert_service,
    ):

        self.alert_service = alert_service



    def get_stalled_workflows(
        self,
    ):

        return self.alert_service.stalled_workflows()



    def get_incomplete_workflows(
        self,
    ):

        return self.alert_service.incomplete_workflows()



    def get_overdue_workflows(
        self,
        threshold_seconds=3600,
    ):

        return self.alert_service.overdue_workflows(
            threshold_seconds
        )



    def get_workload_imbalance(
        self,
    ):

        return self.alert_service.workload_imbalance()
