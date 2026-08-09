from dairyos.operations.decisions.models.decision_context import (
    DecisionContext,
)

from dairyos.operations.decisions.services.operations_decision_service import (
    OperationsDecisionService,
)

from dairyos.operations.decisions.services.decision_ranking_service import (
    DecisionRankingService,
)


def test_create_operational_decision():

    service = OperationsDecisionService()

    decision = service.create_decision(
        DecisionContext(
            source="Feed System",
            category="Feed Delay",
            description="Feed delivery delayed",
            operational_impact="Production risk",
        ),
        priority="HIGH",
        owner_action_required=True,
    )

    assert decision.priority.level == "HIGH"
    assert decision.owner_action_required is True


def test_decision_ranking():

    service = OperationsDecisionService()

    low = service.create_decision(
        DecisionContext(
            source="Staff",
            category="Routine Task",
            description="Routine delay",
            operational_impact="Low",
        ),
        priority="LOW",
    )

    critical = service.create_decision(
        DecisionContext(
            source="Health",
            category="Animal Emergency",
            description="Emergency veterinary issue",
            operational_impact="High",
        ),
        priority="CRITICAL",
    )

    ranked = DecisionRankingService().rank(
        [low, critical]
    )

    assert ranked[0].priority.level == "CRITICAL"

