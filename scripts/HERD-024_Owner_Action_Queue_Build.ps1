New-Item -ItemType Directory -Force dairyos\herd\dashboard\models | Out-Null
New-Item -ItemType Directory -Force dairyos\herd\dashboard\services | Out-Null
New-Item -ItemType Directory -Force tests\core | Out-Null


@'
from dataclasses import dataclass


@dataclass
class OwnerAction:

    priority: int

    category: str

    action: str

    urgency: str

    business_impact: str
'@ | Set-Content dairyos\herd\dashboard\models\owner_action.py



@'
from ..models.owner_action import OwnerAction


class OwnerActionService:


    def generate(

        self,

        command_center

    ):


        actions = []


        if command_center.decision_required:


            actions.append(

                OwnerAction(

                    priority=1,

                    category="EXECUTIVE DECISION",

                    action=command_center.recommended_action,

                    urgency=command_center.time_horizon,

                    business_impact=command_center.business_impact

                )

            )


        else:


            actions.append(

                OwnerAction(

                    priority=3,

                    category="OPERATIONS",

                    action="Maintain current operations",

                    urgency="Routine",

                    business_impact="No immediate risk"

                )

            )


        return sorted(

            actions,

            key=lambda x: x.priority

        )
'@ | Set-Content dairyos\herd\dashboard\services\owner_action_service.py



@'
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
'@ | Set-Content tests\core\test_herd_owner_action.py


Write-Host "HERD-024 Owner Action Queue Intelligence Build Complete"