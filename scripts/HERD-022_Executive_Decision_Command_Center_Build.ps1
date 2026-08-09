New-Item -ItemType Directory -Force dairyos\herd\dashboard\models | Out-Null
New-Item -ItemType Directory -Force dairyos\herd\dashboard\services | Out-Null
New-Item -ItemType Directory -Force tests\core | Out-Null


@'
from dataclasses import dataclass


@dataclass
class ExecutiveDecision:

    farm_name: str

    decision_required: bool

    priority_level: str

    risk_level: str

    recommended_action: str

    business_impact: str

    time_horizon: str
'@ | Set-Content dairyos\herd\dashboard\models\executive_decision.py



@'
from ..models.executive_decision import ExecutiveDecision


class ExecutiveDecisionService:


    def generate(

        self,

        farm_name,

        alerts=None,

        command=None

    ):


        alerts = alerts or []


        priority = "LOW"

        risk = "LOW"

        decision_required = False

        action = "Maintain current operations"

        impact = "No immediate business impact"

        horizon = "Routine monitoring"



        for alert in alerts:


            if alert.category == "REPLACEMENT":


                decision_required = True

                priority = "HIGH"

                risk = "HIGH"

                action = "Secure replacement animals"

                impact = "Protect future milk production capacity"

                horizon = "Immediate"


                break



            if alert.category == "HEALTH":


                decision_required = True

                priority = "HIGH"

                risk = "MEDIUM"

                action = "Review animal health interventions"

                impact = "Reduce production loss and animal risk"

                horizon = "Immediate"


                break



            if alert.category == "REPRODUCTION":


                decision_required = True

                priority = "MEDIUM"

                risk = "MEDIUM"

                action = "Review breeding performance"

                impact = "Protect future herd productivity"

                horizon = "30 days"



        return ExecutiveDecision(

            farm_name=farm_name,

            decision_required=decision_required,

            priority_level=priority,

            risk_level=risk,

            recommended_action=action,

            business_impact=impact,

            time_horizon=horizon

        )
'@ | Set-Content dairyos\herd\dashboard\services\executive_decision_service.py



@'
from dairyos.herd.dashboard.services.executive_decision_service import ExecutiveDecisionService

from dairyos.herd.dashboard.models.executive_alert import ExecutiveAlert



def test_executive_decision_creation():

    decision = ExecutiveDecisionService().generate(

        "Trident Dairies"

    )

    assert decision.farm_name == "Trident Dairies"



def test_replacement_decision():

    alert = ExecutiveAlert(

        category="REPLACEMENT",

        priority=1,

        severity_score=100,

        issue="Replacement shortage",

        recommended_action="Secure replacement animals"

    )


    decision = ExecutiveDecisionService().generate(

        "Trident Dairies",

        [alert]

    )


    assert decision.decision_required is True

    assert decision.priority_level == "HIGH"

    assert decision.risk_level == "HIGH"



def test_health_decision():

    alert = ExecutiveAlert(

        category="HEALTH",

        priority=2,

        severity_score=80,

        issue="Health alerts",

        recommended_action="Review animal health"

    )


    decision = ExecutiveDecisionService().generate(

        "Trident Dairies",

        [alert]

    )


    assert decision.recommended_action == "Review animal health interventions"



def test_no_decision_required():

    decision = ExecutiveDecisionService().generate(

        "Trident Dairies"

    )


    assert decision.decision_required is False
'@ | Set-Content tests\core\test_herd_executive_decision.py


Write-Host "HERD-022 Executive Decision Command Center Build Complete"