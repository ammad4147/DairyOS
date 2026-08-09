$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-033 Command Center Dashboard Consolidation Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class CommandCenterDashboard:


    farm_name: str

    farm_status: str

    health_score: int

    production_score: int

    reproduction_score: int

    financial_score: int

    pending_actions: int

    recommendations_count: int

    historical_actions: int

    effectiveness_score: int

    priority_message: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\command_center_dashboard.py"



@'
from ..models.command_center_dashboard import CommandCenterDashboard



class CommandCenterDashboardService:



    def generate(

        self,

        executive_report,

        recommendations_count=0,

        historical_actions=0

    ):


        return CommandCenterDashboard(

            farm_name=executive_report.farm_name,

            farm_status=executive_report.farm_status,

            health_score=executive_report.health_score,

            production_score=executive_report.production_score,

            reproduction_score=executive_report.reproduction_score,

            financial_score=executive_report.financial_score,

            pending_actions=executive_report.pending_actions,

            recommendations_count=recommendations_count,

            historical_actions=historical_actions,

            effectiveness_score=executive_report.management_effectiveness,

            priority_message=executive_report.priority_message

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\command_center_dashboard_service.py"



@'
from dairyos.herd.dashboard.services.command_center_dashboard_service import CommandCenterDashboardService
from dairyos.herd.dashboard.services.executive_reporting_service import ExecutiveReportingService



def create_report():

    return ExecutiveReportingService().generate(

        "Trident Dairies",

        95,

        90,

        88,

        92,

        3,

        85,

        "Review replacement pipeline"

    )



def test_dashboard_creation():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.farm_name == "Trident Dairies"



def test_dashboard_status():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.farm_status == "GREEN"



def test_health_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.health_score == 95



def test_action_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.pending_actions == 3



def test_recommendation_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report(),

        recommendations_count=5

    )

    assert dashboard.recommendations_count == 5



def test_history_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report(),

        historical_actions=20

    )

    assert dashboard.historical_actions == 20



def test_effectiveness_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.effectiveness_score == 85



def test_priority_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.priority_message == "Review replacement pipeline"



def test_finance_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.financial_score == 92



def test_complete_dashboard_payload():

    dashboard = CommandCenterDashboardService().generate(

        create_report(),

        recommendations_count=4,

        historical_actions=15

    )

    assert dashboard.historical_actions == 15
'@ | Set-Content `
"tests\core\test_command_center_dashboard.py"



Write-Host "HERD-033 Command Center Dashboard Consolidation Build Complete"