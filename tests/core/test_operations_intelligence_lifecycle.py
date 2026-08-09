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


def test_operations_intelligence_lifecycle():

    intelligence = OperationsIntelligenceService()

    signal = OperationalSignal(
        signal_id="SIG-001",
        category="FEED",
        description="Feed delay detected",
        severity="HIGH",
        source="Automation",
        created_at=None,
    )

    registered_signal = intelligence.register_signal(signal)

    assert registered_signal.category == "FEED"
    assert len(intelligence.active_signals()) == 1


    decision_service = OperationsDecisionService()

    decision = decision_service.create_decision(
        context=DecisionContext(
            source="Automation",
            category="FEED_DELAY",
            description="Secure alternate feed supply",
            operational_impact="Milk production risk",
        ),
        priority="HIGH",
        owner_action_required=True,
    )

    assert decision.priority.level == "HIGH"


    action_service = OperationalActionService()

    action = action_service.create_action(
        title=decision.title,
        description=decision.description,
        assigned_to="Supervisor",
        department="Feed",
    )

    assert action.status.status == "OPEN"


    feedback_service = FeedbackService()

    feedback = feedback_service.create_feedback(
        worked="Alternate supplier arranged",
        failed="Initial supplier delayed",
        improvement="Maintain backup supplier",
    )

    outcome_service = OutcomeRecordService()

    outcome = outcome_service.record_outcome(
        action_id=action.action_id,
        result="Feed restored",
        rating="GOOD",
        feedback=feedback,
    )

    assert outcome.rating.rating == "GOOD"
    assert outcome.feedback.improvement == "Maintain backup supplier"
