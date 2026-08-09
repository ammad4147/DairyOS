$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-026 Farm Command Center Integration Build"

New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null


@'
from dataclasses import dataclass


@dataclass
class FarmCommandCenter:

    farm_name: str

    operational_status: str

    risk_level: str

    executive_score: int

    priorities: list

    owner_actions: list

    active_alerts: int
'@ | Set-Content `
"dairyos\herd\dashboard\models\farm_command_center.py"


@'
from ..models.farm_command_center import FarmCommandCenter


class FarmCommandCenterService:


    def generate(

        self,

        executive_decision,

        daily_board

    ):


        status = "STABLE"


        if executive_decision.risk_level == "HIGH":

            status = "ATTENTION REQUIRED"


        elif executive_decision.risk_level == "MEDIUM":

            status = "MONITOR"



        priorities = []

        priorities.extend(

            executive_decision.recommendations

        )


        actions = []

        actions.extend(

            daily_board.owner_actions

        )



        return FarmCommandCenter(

            farm_name=daily_board.farm_name,

            operational_status=status,

            risk_level=executive_decision.risk_level,

            executive_score=getattr(

                executive_decision,

                "decision_score",

                0

            ),

            priorities=priorities,

            owner_actions=actions,

            active_alerts=len(actions)

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\farm_command_center_service.py"



@'
from dairyos.herd.dashboard.models.farm_command_center import FarmCommandCenter
from dairyos.herd.dashboard.services.farm_command_center_service import FarmCommandCenterService


class DummyDecision:

    risk_level = "LOW"

    recommendations = [

        "Maintain herd operations"

    ]

    decision_score = 90



class DummyBoard:

    farm_name = "Trident Dairies"

    owner_actions = []



def test_command_center_creation():

    center = FarmCommandCenter(

        farm_name="Trident Dairies",

        operational_status="STABLE",

        risk_level="LOW",

        executive_score=90,

        priorities=[],

        owner_actions=[],

        active_alerts=0

    )


    assert center.farm_name == "Trident Dairies"



def test_command_center_service():

    center = FarmCommandCenterService().generate(

        DummyDecision(),

        DummyBoard()

    )


    assert center.operational_status == "STABLE"



def test_high_risk_status():

    decision = DummyDecision()

    decision.risk_level = "HIGH"


    center = FarmCommandCenterService().generate(

        decision,

        DummyBoard()

    )


    assert center.operational_status == "ATTENTION REQUIRED"



def test_priority_flow():

    center = FarmCommandCenterService().generate(

        DummyDecision(),

        DummyBoard()

    )


    assert len(center.priorities) == 1



def test_owner_action_flow():

    center = FarmCommandCenterService().generate(

        DummyDecision(),

        DummyBoard()

    )


    assert center.owner_actions == []



def test_score_flow():

    center = FarmCommandCenterService().generate(

        DummyDecision(),

        DummyBoard()

    )


    assert center.executive_score == 90



def test_risk_flow():

    center = FarmCommandCenterService().generate(

        DummyDecision(),

        DummyBoard()

    )


    assert center.risk_level == "LOW"



def test_alert_count():

    center = FarmCommandCenterService().generate(

        DummyDecision(),

        DummyBoard()

    )


    assert center.active_alerts == 0
'@ | Set-Content `
"tests\core\test_farm_command_center.py"


Write-Host "HERD-026 Farm Command Center Integration Build Complete"