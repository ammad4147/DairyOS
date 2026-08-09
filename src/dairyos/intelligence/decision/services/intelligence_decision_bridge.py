from dairyos.intelligence.models.intelligence_recommendation import (
    IntelligenceRecommendation,
)

from dairyos.operations.decisions.models.decision_context import (
    DecisionContext,
)

from dairyos.operations.decisions.services.operations_decision_service import (
    OperationsDecisionService,
)

from dairyos.operations.workflow.models.operational_workflow_event import (
    OperationalWorkflowEvent,
)

from dairyos.operations.workflow.services.operations_workflow_orchestrator import (
    OperationsWorkflowOrchestrator,
)


class IntelligenceDecisionBridge:
    """
    Converts intelligence recommendations into
    operational decisions and workflow events.

    Rules:

    Intelligence:
        observes
        analyses
        recommends

    Decision layer:
        creates operational decisions

    Workflow layer:
        tracks lifecycle

    This bridge never:
        - executes actions
        - mutates farm state
        - bypasses human accountability
    """


    def __init__(
        self,
        decision_service=None,
        workflow_orchestrator=None,
    ):

        self.decision_service = (
            decision_service
            if decision_service is not None
            else OperationsDecisionService()
        )


        self.workflow_orchestrator = (
            workflow_orchestrator
            if workflow_orchestrator is not None
            else OperationsWorkflowOrchestrator()
        )



    def create_operational_decision(
        self,
        recommendation: IntelligenceRecommendation,
    ):

        context = DecisionContext(

            source=
                recommendation.source_signal,

            category=
                recommendation.recommendation_type,

            description=
                recommendation.action,

            operational_impact=
                recommendation.reasoning,

        )


        decision = (
            self.decision_service
            .create_decision(
                context=context,
                priority=recommendation.priority,
                owner_action_required=True,
            )
        )


        workflow_event = OperationalWorkflowEvent(

            event_id=
                decision.decision_id,

            source=
                "INTELLIGENCE",

            category=
                decision.title,

            priority=
                recommendation.priority,

            description=
                recommendation.action,

            created_at=
                recommendation.created_at,

        )


        self.workflow_orchestrator.submit_event(
            workflow_event
        )


        return {

            "decision":
                decision,

            "workflow_event":
                workflow_event,

        }
