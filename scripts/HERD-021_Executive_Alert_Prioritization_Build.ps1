$root = "C:\DairyOS"

Write-Host "Starting HERD-021 Executive Alert Prioritization Build..." -ForegroundColor Cyan


# Executive alert model

@'
from dataclasses import dataclass



@dataclass
class ExecutiveAlert:


    category: str

    priority: int

    impact: str

    urgency: str

    message: str

    recommended_action: str
'@ | Set-Content `
"$root\dairyos\herd\dashboard\models\executive_alert.py"



# Alert prioritization service

@'
from ..models.executive_alert import ExecutiveAlert



class AlertPriorityService:



    def generate(

        self,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False,

        production_issue=False

    ):


        alerts = []



        if replacement_shortage:

            alerts.append(

                ExecutiveAlert(

                    category="REPLACEMENT",

                    priority=1,

                    impact="HIGH",

                    urgency="IMMEDIATE",

                    message="Replacement pipeline shortage detected",

                    recommended_action="Review heifer retention strategy"

                )

            )



        if health_alerts > 0:

            alerts.append(

                ExecutiveAlert(

                    category="HEALTH",

                    priority=2,

                    impact="HIGH",

                    urgency="TODAY",

                    message="Animal health alerts require review",

                    recommended_action="Review health records"

                )

            )



        if open_cows > 3:

            alerts.append(

                ExecutiveAlert(

                    category="REPRODUCTION",

                    priority=3,

                    impact="MEDIUM",

                    urgency="THIS WEEK",

                    message="Reproductive performance requires attention",

                    recommended_action="Review open cow list"

                )

            )



        if production_issue:

            alerts.append(

                ExecutiveAlert(

                    category="PRODUCTION",

                    priority=4,

                    impact="MEDIUM",

                    urgency="MONITOR",

                    message="Production performance deviation",

                    recommended_action="Review milk production"

                )

            )



        return sorted(

            alerts,

            key=lambda x: x.priority

        )
'@ | Set-Content `
"$root\dairyos\herd\dashboard\services\alert_priority_service.py"



# Extend cockpit model

@'
from dataclasses import dataclass, field



@dataclass
class ExecutiveCockpit:


    farm_name: str

    overall_score: int

    health_score: int

    production_score: int

    reproduction_score: int

    financial_score: int

    risk_level: str

    priority: str

    summary: str

    actions: list = field(default_factory=list)

    alerts: list = field(default_factory=list)
'@ | Set-Content `
"$root\dairyos\herd\dashboard\models\executive_cockpit.py"



# Update cockpit service integration

@'
from ..models.executive_cockpit import ExecutiveCockpit

from .alert_priority_service import AlertPriorityService



class ExecutiveCockpitService:



    def generate(

        self,

        command,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False

    ):


        health = 100 if health_alerts == 0 else 80 if health_alerts <= 2 else 60

        reproduction = 100 if open_cows <= 3 else 75 if open_cows <= 6 else 50

        financial = 100 if command.financial_status == "POSITIVE" else 70

        production = 100 if command.production_status == "ACTIVE" else 80

        replacement = 50 if replacement_shortage else 100



        overall = round(

            (

                health

                + reproduction

                + financial

                + production

                + replacement

            ) / 5

        )



        risk = command.overall_risk



        alerts = AlertPriorityService().generate(

            health_alerts,

            open_cows,

            replacement_shortage

        )



        return ExecutiveCockpit(

            farm_name=command.farm_name,

            overall_score=overall,

            health_score=health,

            production_score=production,

            reproduction_score=reproduction,

            financial_score=financial,

            risk_level=risk,

            priority=alerts[0].recommended_action if alerts else "Maintain operations",

            summary=f"Executive herd score {overall}/100",

            alerts=alerts

        )
'@ | Set-Content `
"$root\dairyos\herd\dashboard\services\executive_cockpit_service.py"



# Tests

@'
from dairyos.herd.dashboard.services.alert_priority_service import AlertPriorityService



def test_alert_creation():

    alerts = AlertPriorityService().generate(

        health_alerts=1

    )

    assert len(alerts) == 1



def test_replacement_priority():

    alerts = AlertPriorityService().generate(

        replacement_shortage=True

    )

    assert alerts[0].priority == 1



def test_health_priority():

    alerts = AlertPriorityService().generate(

        health_alerts=2

    )

    assert alerts[0].category == "HEALTH"



def test_reproduction_priority():

    alerts = AlertPriorityService().generate(

        open_cows=5

    )

    assert alerts[0].category == "REPRODUCTION"



def test_alert_ordering():

    alerts = AlertPriorityService().generate(

        health_alerts=1,

        replacement_shortage=True

    )

    assert alerts[0].category == "REPLACEMENT"



def test_cockpit_alert_integration():

    alerts = AlertPriorityService().generate(

        replacement_shortage=True

    )

    assert len(alerts) == 1



def test_no_alerts():

    alerts = AlertPriorityService().generate()

    assert len(alerts) == 0



def test_owner_action_queue():

    alerts = AlertPriorityService().generate(

        open_cows=7

    )

    assert alerts[0].recommended_action == "Review open cow list"
'@ | Set-Content `
"$root\tests\core\test_herd_alert_priority.py"



Write-Host ""
Write-Host "HERD-021 Build Completed Successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Validation:"
Write-Host "pytest tests/core/test_herd_alert_priority.py -v"
Write-Host "pytest -q"