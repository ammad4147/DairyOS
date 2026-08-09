from dairyos.operations.executive_decision.services.executive_decision_service import (
    ExecutiveDecisionService,
)

from dairyos.operations.executive_decision.services.decision_action_service import (
    DecisionActionService,
)

from dairyos.operations.executive_decision.models.decision_urgency import (
    DecisionUrgency,
)



def test_critical_executive_decision():

    service = ExecutiveDecisionService()


    decision = service.create_decision(
        "DEC-001",
        "Milk Production Decline",
        30,
    )


    assert decision.urgency == DecisionUrgency.CRITICAL



def test_decision_action_required():

    service = ExecutiveDecisionService()


    decision = service.create_decision(
        "DEC-002",
        "Feed Cost Increase",
        55,
    )


    action_service = DecisionActionService()


    assert action_service.requires_action(decision) is True
