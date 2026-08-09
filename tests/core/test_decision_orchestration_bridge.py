from dairyos.intelligence.decision.models.decision_recommendation import (
    DecisionRecommendation,
)

from dairyos.intelligence.operations.orchestration.gateway.operations_orchestration_gateway import (
    OperationsOrchestrationGateway,
)

from dairyos.intelligence.operations.orchestration.integration.decision_orchestration_bridge import (
    DecisionOrchestrationBridge,
)


def test_bridge_creates_operational_actions():

    recommendation = DecisionRecommendation(
        category="feeding",
        recommendation="Increase feed allocation",
        rationale="Low feed intake detected",
        confidence=0.96,
        priority="high",
    )

    bridge = DecisionOrchestrationBridge(
        OperationsOrchestrationGateway()
    )

    actions = bridge.create_actions(
        [
            {
                "recommendation": recommendation,
                "confidence": None,
            }
        ]
    )

    assert len(actions) == 1

    action = actions[0]

    assert action.action_type == "feeding"
    assert action.description == "Increase feed allocation"
    assert action.priority == "high"
    assert action.status == "pending"
