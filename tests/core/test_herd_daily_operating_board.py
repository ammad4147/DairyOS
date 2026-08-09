from dairyos.herd.dashboard.services.daily_operating_board_service import DailyOperatingBoardService

from dairyos.herd.dashboard.models.executive_command_center import ExecutiveCommandCenter

from dairyos.herd.dashboard.models.owner_action import OwnerAction



def test_daily_board_creation():


    center = ExecutiveCommandCenter(

        farm_name="Trident Dairies",

        overall_score=90,

        risk_level="LOW",

        decision_required=False,

        priority_level="LOW",

        top_decision="Maintain current operations",

        recommended_action="Maintain current operations",

        business_impact="No immediate business impact",

        time_horizon="Routine"

    )


    action = OwnerAction(

        priority=3,

        category="OPERATIONS",

        action="Maintain current operations",

        urgency="Routine",

        business_impact="No immediate risk"

    )


    board = DailyOperatingBoardService().generate(

        center,

        [action]

    )


    assert board.farm_name == "Trident Dairies"

    assert board.operating_status == "STABLE"



def test_daily_board_risk():


    center = ExecutiveCommandCenter(

        farm_name="Trident Dairies",

        overall_score=70,

        risk_level="HIGH",

        decision_required=True,

        priority_level="HIGH",

        top_decision="Secure replacement animals",

        recommended_action="Secure replacement animals",

        business_impact="Protect production",

        time_horizon="Immediate"

    )


    board = DailyOperatingBoardService().generate(

        center,

        []

    )


    assert board.operating_status == "ATTENTION REQUIRED"

    assert board.risk_count == 1

    assert board.pending_decisions == 1
