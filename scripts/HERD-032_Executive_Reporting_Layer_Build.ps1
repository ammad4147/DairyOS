$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-032 Executive Reporting Layer Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class ExecutiveReport:


    farm_name: str

    farm_status: str

    health_score: int

    production_score: int

    reproduction_score: int

    financial_score: int

    pending_actions: int

    management_effectiveness: int

    priority_message: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\executive_report.py"



@'
from ..models.executive_report import ExecutiveReport



class ExecutiveReportingService:



    def generate(

        self,

        farm_name,

        health_score,

        production_score,

        reproduction_score,

        financial_score,

        pending_actions,

        effectiveness,

        priority_message

    ):



        overall = round(

            (

                health_score

                + production_score

                + reproduction_score

                + financial_score

                + effectiveness

            ) / 5

        )



        if overall >= 85:

            status = "GREEN"

        elif overall >= 70:

            status = "YELLOW"

        else:

            status = "RED"



        return ExecutiveReport(

            farm_name=farm_name,

            farm_status=status,

            health_score=health_score,

            production_score=production_score,

            reproduction_score=reproduction_score,

            financial_score=financial_score,

            pending_actions=pending_actions,

            management_effectiveness=effectiveness,

            priority_message=priority_message

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\executive_reporting_service.py"



@'
from dairyos.herd.dashboard.services.executive_reporting_service import ExecutiveReportingService



def test_report_creation():

    report = ExecutiveReportingService().generate(

        "Trident Dairies",

        95,

        90,

        88,

        92,

        3,

        85,

        "Review replacement pipeline"

    )

    assert report.farm_name == "Trident Dairies"



def test_green_status():

    report = ExecutiveReportingService().generate(

        "Farm",

        95,

        95,

        95,

        95,

        0,

        95,

        "Maintain operations"

    )

    assert report.farm_status == "GREEN"



def test_yellow_status():

    report = ExecutiveReportingService().generate(

        "Farm",

        75,

        75,

        75,

        75,

        5,

        75,

        "Monitor"

    )

    assert report.farm_status == "YELLOW"



def test_red_status():

    report = ExecutiveReportingService().generate(

        "Farm",

        50,

        50,

        50,

        50,

        10,

        50,

        "Immediate action"

    )

    assert report.farm_status == "RED"



def test_pending_actions():

    report = ExecutiveReportingService().generate(

        "Farm",

        90,

        90,

        90,

        90,

        4,

        90,

        "Review"

    )

    assert report.pending_actions == 4



def test_priority_message():

    report = ExecutiveReportingService().generate(

        "Farm",

        90,

        90,

        90,

        90,

        1,

        90,

        "Check health"

    )

    assert report.priority_message == "Check health"



def test_effectiveness():

    report = ExecutiveReportingService().generate(

        "Farm",

        90,

        90,

        90,

        90,

        1,

        90,

        "Stable"

    )

    assert report.management_effectiveness == 90



def test_report_scores():

    report = ExecutiveReportingService().generate(

        "Farm",

        80,

        80,

        80,

        80,

        1,

        80,

        "Stable"

    )

    assert report.health_score == 80



def test_report_model():

    report = ExecutiveReportingService().generate(

        "Farm",

        100,

        100,

        100,

        100,

        0,

        100,

        "Excellent"

    )

    assert report.farm_status == "GREEN"



def test_report_complete():

    report = ExecutiveReportingService().generate(

        "Farm",

        85,

        85,

        85,

        85,

        2,

        85,

        "Continue"

    )

    assert report.pending_actions == 2
'@ | Set-Content `
"tests\core\test_executive_reporting.py"



Write-Host "HERD-032 Executive Reporting Layer Build Complete"