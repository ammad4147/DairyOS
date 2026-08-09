from dairyos.herd.dashboard.services.executive_command_center_service import ExecutiveCommandCenterService

from dairyos.herd.dashboard.models.executive_cockpit import ExecutiveCockpit

from dairyos.herd.dashboard.models.executive_decision import ExecutiveDecision



def test_command_center_creation():


    cockpit = ExecutiveCockpit(

        farm_name="Trident Dairies",

        overall_score=90,

        health_score=100,

        production_score=100,

        reproduction_score=100,

        financial_score=100,

        risk_level="LOW",

        priority="Maintain operations",

        summary="Stable",

        alerts=[]

    )


    decision = ExecutiveDecision(

        farm_name="Trident Dairies",

        decision_required=False,

        priority_level="LOW",

        risk_level="LOW",

        recommended_action="Maintain current operations",

        business_impact="No immediate business impact",

        time_horizon="Routine monitoring"

    )


    result = ExecutiveCommandCenterService().generate(

        cockpit,

        decision

    )


    assert result.farm_name == "Trident Dairies"

    assert result.overall_score == 90



def test_high_priority_command_center():


    cockpit = ExecutiveCockpit(

        farm_name="Trident Dairies",

        overall_score=70,

        health_score=80,

        production_score=80,

        reproduction_score=50,

        financial_score=70,

        risk_level="HIGH",

        priority="Replacement",

        summary="Risk",

        alerts=[]

    )


    decision = ExecutiveDecision(

        farm_name="Trident Dairies",

        decision_required=True,

        priority_level="HIGH",

        risk_level="HIGH",

        recommended_action="Secure replacement animals",

        business_impact="Protect future milk production capacity",

        time_horizon="Immediate"

    )


    result = ExecutiveCommandCenterService().generate(

        cockpit,

        decision

    )


    assert result.decision_required is True

    assert result.priority_level == "HIGH"

    assert result.top_decision == "Secure replacement animals"
