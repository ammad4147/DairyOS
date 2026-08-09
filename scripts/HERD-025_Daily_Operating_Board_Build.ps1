New-Item -ItemType Directory -Force dairyos\herd\dashboard\models | Out-Null
New-Item -ItemType Directory -Force dairyos\herd\dashboard\services | Out-Null
New-Item -ItemType Directory -Force tests\core | Out-Null


@'
from dataclasses import dataclass


@dataclass
class DailyOperatingBoard:

    farm_name: str

    operating_status: str

    critical_tasks: list

    risk_count: int

    pending_decisions: int
'@ | Set-Content dairyos\herd\dashboard\models\daily_operating_board.py



@'
from ..models.daily_operating_board import DailyOperatingBoard


class DailyOperatingBoardService:


    def generate(

        self,

        command_center,

        actions

    ):


        critical_tasks = []


        for action in actions:

            critical_tasks.append(

                {

                    "priority": action.priority,

                    "category": action.category,

                    "action": action.action,

                    "urgency": action.urgency

                }

            )



        risk_count = 0

        if command_center.risk_level != "LOW":

            risk_count = 1



        pending_decisions = (

            1

            if command_center.decision_required

            else 0

        )



        status = (

            "ATTENTION REQUIRED"

            if risk_count > 0

            else "STABLE"

        )



        return DailyOperatingBoard(

            farm_name=command_center.farm_name,

            operating_status=status,

            critical_tasks=critical_tasks,

            risk_count=risk_count,

            pending_decisions=pending_decisions

        )
'@ | Set-Content dairyos\herd\dashboard\services\daily_operating_board_service.py



@'
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
'@ | Set-Content tests\core\test_herd_daily_operating_board.py


Write-Host "HERD-025 Daily Operating Board Build Complete"