class WorkflowIntelligenceQueryGateway:
    """
    Integration boundary for workflow intelligence queries.

    Exposes dashboard-safe read operations
    without exposing intelligence internals.
    """


    def __init__(
        self,
        query_service,
    ):

        self.query_service = query_service



    def get_workflow(
        self,
        workflow_id: str,
    ):

        return self.query_service.get(
            workflow_id
        )



    def get_all_workflows(
        self,
    ):

        return self.query_service.all()



    def get_workflow_count(
        self,
    ):

        return self.query_service.count()



    def get_workflows_by_status(
        self,
        status: str,
    ):

        return self.query_service.by_status(
            status
        )



    def get_active_workflows(
        self,
    ):

        return self.query_service.active()
