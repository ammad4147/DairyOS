from dairyos.intelligence.integration.executive_decision_bridge import (
    ExecutiveDecisionBridge,
)

from dairyos.herd.dashboard.models.executive_command_center import (
    ExecutiveCommandCenter,
)



def test_executive_decision_bridge_builds_decision():


    command = ExecutiveCommandCenter(

        farm_name="Trident Dairies",

        overall_score=85,

        risk_level="HIGH",

        decision_required=True,

        priority_level="HIGH",

        top_decision="Replacement decision required",

        recommended_action="Secure replacement animals",

        business_impact="Protect milk production",

        time_horizon="Immediate",
    )


    bridge = ExecutiveDecisionBridge()


    decision = bridge.build_decision(
        command
    )


    assert decision.farm_name == "Trident Dairies"

    assert decision.decision_required is True

    assert decision.priority_level == "HIGH"

    assert decision.time_horizon == "Immediate"
