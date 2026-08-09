$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-045 Preventive Action Planner Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class PreventiveActionPlan:


    category: str

    risk_level: str

    priority: str

    actions: list

    timeline: str

    owner_attention: bool
'@ | Set-Content `
"dairyos\herd\dashboard\models\preventive_action_plan.py"



@'
from ..models.preventive_action_plan import PreventiveActionPlan



class PreventiveActionService:



    def create_plan(

        self,

        category,

        risk_level

    ):


        priority = self._priority(

            risk_level

        )


        return PreventiveActionPlan(

            category,

            risk_level,

            priority,

            self._actions(category),

            self._timeline(risk_level),

            risk_level in (

                "HIGH",

                "CRITICAL"

            )

        )



    def _priority(

        self,

        risk_level

    ):


        priorities = {

            "CRITICAL": "URGENT",

            "HIGH": "HIGH",

            "MEDIUM": "NORMAL",

            "LOW": "LOW"

        }


        return priorities.get(

            risk_level,

            "NORMAL"

        )



    def _actions(

        self,

        category

    ):


        actions = {

            "PRODUCTION":

                [

                    "Review feed quality",

                    "Check production records",

                    "Review health indicators"

                ],


            "HEALTH":

                [

                    "Review animal health status",

                    "Check preventive measures",

                    "Schedule assessment"

                ],


            "REPRODUCTION":

                [

                    "Review breeding performance",

                    "Check conception indicators",

                    "Assess reproductive plan"

                ],


            "FINANCE":

                [

                    "Review financial trends",

                    "Assess cost drivers",

                    "Update planning"

                ]

        }


        return actions.get(

            category,

            [

                "Review farm indicators"

            ]

        )



    def _timeline(

        self,

        risk_level

    ):


        if risk_level in (

            "HIGH",

            "CRITICAL"

        ):

            return "Within 7 days"


        return "Monitor regularly"
'@ | Set-Content `
"dairyos\herd\dashboard\services\preventive_action_service.py"



@'
from dairyos.herd.dashboard.services.preventive_action_service import PreventiveActionService



def test_plan_creation():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "HIGH"

    )

    assert plan.category == "PRODUCTION"



def test_high_priority():

    plan = PreventiveActionService().create_plan(

        "HEALTH",

        "HIGH"

    )

    assert plan.priority == "HIGH"



def test_critical_priority():

    plan = PreventiveActionService().create_plan(

        "FINANCE",

        "CRITICAL"

    )

    assert plan.priority == "URGENT"



def test_low_priority():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "LOW"

    )

    assert plan.priority == "LOW"



def test_owner_attention():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "HIGH"

    )

    assert plan.owner_attention



def test_no_owner_attention():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "LOW"

    )

    assert not plan.owner_attention



def test_production_actions():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "HIGH"

    )

    assert "Review feed quality" in plan.actions



def test_health_actions():

    plan = PreventiveActionService().create_plan(

        "HEALTH",

        "HIGH"

    )

    assert "Review animal health status" in plan.actions



def test_timeline():

    plan = PreventiveActionService().create_plan(

        "PRODUCTION",

        "HIGH"

    )

    assert plan.timeline == "Within 7 days"



def test_model():

    plan = PreventiveActionService().create_plan(

        "FINANCE",

        "MEDIUM"

    )

    assert plan.risk_level == "MEDIUM"
'@ | Set-Content `
"tests\core\test_preventive_action.py"



Write-Host "HERD-045 Preventive Action Planner Build Complete"