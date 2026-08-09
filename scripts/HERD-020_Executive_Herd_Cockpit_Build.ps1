$root = "C:\DairyOS"

Write-Host "Starting HERD-020 Executive Herd Cockpit Build..." -ForegroundColor Cyan


# Create executive cockpit model

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
'@ | Set-Content `
"$root\dairyos\herd\dashboard\models\executive_cockpit.py"



# Create executive cockpit service

@'
from ..models.executive_cockpit import ExecutiveCockpit



class ExecutiveCockpitService:



    def calculate_health_score(

        self,

        health_alerts

    ):

        if health_alerts == 0:

            return 100

        if health_alerts <= 2:

            return 80

        return 60



    def calculate_reproduction_score(

        self,

        open_cows

    ):

        if open_cows <= 3:

            return 100

        if open_cows <= 6:

            return 75

        return 50



    def calculate_financial_score(

        self,

        financial_status

    ):

        if financial_status == "POSITIVE":

            return 100

        if financial_status == "WARNING":

            return 70

        return 40



    def calculate_replacement_score(

        self,

        shortage

    ):

        return 50 if shortage else 100



    def generate(

        self,

        command,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False

    ):


        health = self.calculate_health_score(

            health_alerts

        )


        reproduction = self.calculate_reproduction_score(

            open_cows

        )


        financial = self.calculate_financial_score(

            command.financial_status

        )


        replacement = self.calculate_replacement_score(

            replacement_shortage

        )


        production = 100 if command.production_status == "ACTIVE" else 80



        overall = round(

            (

                health

                + production

                + reproduction

                + financial

                + replacement

            ) / 5

        )


        risk = "LOW"

        priority = "Maintain operations"


        if overall < 80:

            risk = "MEDIUM"

            priority = "Review operational risks"


        if command.overall_risk == "HIGH":

            risk = "HIGH"

            priority = command.owner_attention



        return ExecutiveCockpit(

            farm_name=command.farm_name,

            overall_score=overall,

            health_score=health,

            production_score=production,

            reproduction_score=reproduction,

            financial_score=financial,

            risk_level=risk,

            priority=priority,

            summary=f"Executive herd score {overall}/100",

            actions=command.recommended_actions

        )
'@ | Set-Content `
"$root\dairyos\herd\dashboard\services\executive_cockpit_service.py"



# Create tests

@'
from dairyos.herd.dashboard.models.herd_command import HerdCommand

from dairyos.herd.dashboard.services.executive_cockpit_service import ExecutiveCockpitService



def command():


    return HerdCommand(

        farm_name="Trident Dairies",

        total_animals=100,

        production_status="ACTIVE",

        health_status="NORMAL",

        reproduction_status="NORMAL",

        financial_status="POSITIVE",

        overall_risk="LOW",

        owner_attention="",

    )



def test_cockpit_creation():

    cockpit = ExecutiveCockpitService().generate(

        command()

    )

    assert cockpit.farm_name == "Trident Dairies"



def test_health_score():

    service = ExecutiveCockpitService()

    assert service.calculate_health_score(0) == 100



def test_reproduction_score():

    service = ExecutiveCockpitService()

    assert service.calculate_reproduction_score(8) == 50



def test_finance_score():

    service = ExecutiveCockpitService()

    assert service.calculate_financial_score("WARNING") == 70



def test_replacement_score():

    service = ExecutiveCockpitService()

    assert service.calculate_replacement_score(True) == 50



def test_overall_score():

    cockpit = ExecutiveCockpitService().generate(

        command()

    )

    assert cockpit.overall_score == 100



def test_high_risk_summary():

    cmd = command()

    cmd.overall_risk = "HIGH"

    cmd.owner_attention = "Review replacement pipeline"

    cmd.recommended_actions = [

        "Review replacement pipeline"

    ]

    cockpit = ExecutiveCockpitService().generate(

        cmd,

        replacement_shortage=True

    )

    assert cockpit.risk_level == "HIGH"



def test_command_to_cockpit_flow():

    cockpit = ExecutiveCockpitService().generate(

        command(),

        health_alerts=1,

        open_cows=4

    )

    assert cockpit.health_score == 80

    assert cockpit.reproduction_score == 75
'@ | Set-Content `
"$root\tests\core\test_herd_executive_cockpit.py"



Write-Host ""
Write-Host "HERD-020 Executive Herd Cockpit Build Completed" -ForegroundColor Green
Write-Host ""
Write-Host "Run:"
Write-Host "pytest tests/core/test_herd_executive_cockpit.py -v"
Write-Host "pytest -q"