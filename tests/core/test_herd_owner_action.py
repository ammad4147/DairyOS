from dairyos.herd.dashboard.services.owner_action_service import OwnerActionService

from dairyos.herd.dashboard.models.executive_command_center import ExecutiveCommandCenter



def test_owner_action_creation():


    center = ExecutiveCommandCenter(

        farm_name="Trident Dairies",

        overall_score=90,

        risk_level="LOW",

        decision_required=False,

        priority_level="LOW",

        top_decision="Maintain current operations",

        recommended_action="Maintain current operations",

        business_impact="No immediate business impact",

        time_horizon="Routine monitoring"

    )


    actions = OwnerActionService().generate(center)


    assert len(actions) == 1

    assert actions[0].priority == 3



def test_high_priority_owner_action():


    center = ExecutiveCommandCenter(

        farm_name="Trident Dairies",

        overall_score=70,

        risk_level="HIGH",

        decision_required=True,

        priority_level="HIGH",

        top_decision="Secure replacement animals",

        recommended_action="Secure replacement animals",

        business_impact="Protect future milk production capacity",

        time_horizon="Immediate"

    )


    actions = OwnerActionService().generate(center)


    assert actions[0].priority == 1

    assert actions[0].action == "Secure replacement animals"

    assert actions[0].urgency == "Immediate"
