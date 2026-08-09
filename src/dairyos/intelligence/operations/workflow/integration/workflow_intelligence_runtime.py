from dairyos.intelligence.operations.workflow.repositories.workflow_projection_repository import (
    WorkflowProjectionRepository,
)


from dairyos.intelligence.operations.workflow.services.workflow_projection_service import (
    WorkflowProjectionService,
)


from dairyos.intelligence.operations.workflow.services.workflow_query_service import (
    WorkflowQueryService,
)


from dairyos.intelligence.operations.workflow.services.workflow_analytics_service import (
    WorkflowAnalyticsService,
)


from dairyos.intelligence.operations.workflow.services.workflow_alert_service import (
    WorkflowAlertService,
)


from dairyos.intelligence.operations.workflow.services.workflow_decision_service import (
    WorkflowDecisionService,
)


from dairyos.intelligence.operations.workflow.integration.workflow_intelligence_event_adapter import (
    WorkflowIntelligenceEventAdapter,
)


from dairyos.intelligence.operations.workflow.integration.workflow_intelligence_query_gateway import (
    WorkflowIntelligenceQueryGateway,
)


from dairyos.intelligence.operations.workflow.integration.workflow_intelligence_analytics_gateway import (
    WorkflowIntelligenceAnalyticsGateway,
)


from dairyos.intelligence.operations.workflow.integration.workflow_intelligence_alert_gateway import (
    WorkflowIntelligenceAlertGateway,
)


from dairyos.intelligence.operations.workflow.integration.workflow_intelligence_decision_gateway import (
    WorkflowIntelligenceDecisionGateway,
)



class WorkflowIntelligenceRuntime:
    """
    Runtime container for workflow intelligence.

    Provides operational intelligence boundaries
    for events, queries, analytics, alerts,
    and rule-based decisions.
    """


    def __init__(
        self,
    ):

        self.repository = WorkflowProjectionRepository()


        self.service = WorkflowProjectionService(
            self.repository
        )


        self.event_adapter = WorkflowIntelligenceEventAdapter(
            self.service
        )


        self.query_service = WorkflowQueryService(
            self.repository
        )


        self.query_gateway = WorkflowIntelligenceQueryGateway(
            self.query_service
        )


        self.analytics_service = WorkflowAnalyticsService(
            self.repository
        )


        self.analytics_gateway = WorkflowIntelligenceAnalyticsGateway(
            self.analytics_service
        )


        self.alert_service = WorkflowAlertService(
            self.repository
        )


        self.alert_gateway = WorkflowIntelligenceAlertGateway(
            self.alert_service
        )


        self.decision_service = WorkflowDecisionService(
            self.alert_service
        )


        self.decision_gateway = WorkflowIntelligenceDecisionGateway(
            self.decision_service
        )
