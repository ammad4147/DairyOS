from dairyos.operations.automation.services.automation_execution_service import (
    AutomationExecutionService,
)

from dairyos.operations.intelligence.models.operational_signal import (
    OperationalSignal,
)

from dairyos.operations.intelligence.services.operations_intelligence_service import (
    OperationsIntelligenceService,
)

from dairyos.operations.decisions.models.decision_context import (
    DecisionContext,
)

from dairyos.operations.decisions.services.operations_decision_service import (
    OperationsDecisionService,
)

from dairyos.operations.actions.services.operational_action_service import (
    OperationalActionService,
)

from dairyos.operations.outcomes.services.feedback_service import (
    FeedbackService,
)

from dairyos.operations.outcomes.services.outcome_record_service import (
    OutcomeRecordService,
)


def test_automation_to_learning_flow():

    automation = AutomationExecutionService()

    event = automation.execute(
        trigger="FEED_DELAY"
    )

    assert event.executed is True


    intelligence = OperationsIntelligenceService()

    signal = intelligence.register_signal(
        OperationalSignal(
            signal_id="SIG-AUTO-001",
            category="FEED",
            description=event.description,
            severity="HIGH",
            source="Automation",
            created_at=None,
        )
    )

    assert signal.source == "Automation"


    decisions = OperationsDecisionService()

    decision = decisions.create_decision(
        context=DecisionContext(
            source="Automation",
            category="FEED_DELAY",
            description="Secure alternate feed supply",
            operational_impact="Production protection",
        ),
        priority="HIGH",
        owner_action_required=True,
    )

    assert decision.priority.level == "HIGH"


    actions = OperationalActionService()

    action = actions.create_action(
        title=decision.title,
        description=decision.description,
        assigned_to="Supervisor",
        department="Feed",
    )

    assert action.status.status == "OPEN"


    feedback = FeedbackService().create_feedback(
        worked="Feed restored",
        failed="Supplier delay",
        improvement="Maintain backup stock",
    )


    outcome = OutcomeRecordService().record_outcome(
        action_id=action.action_id,
        result="Resolved",
        rating="EXCELLENT",
        feedback=feedback,
    )


    assert outcome.rating.rating == "EXCELLENT"
