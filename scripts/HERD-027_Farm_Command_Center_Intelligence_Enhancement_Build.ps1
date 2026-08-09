$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-027 Farm Command Center Intelligence Enhancement"

New-Item -ItemType Directory -Force -Path `
"dairyos\herd\dashboard\models",
"dairyos\herd\dashboard\services",
"tests\core" | Out-Null


@'
from dataclasses import dataclass


@dataclass
class FarmHealthIndex:

    production_score: int

    health_score: int

    reproduction_score: int

    financial_score: int

    overall_score: int
'@ | Set-Content `
"dairyos\herd\dashboard\models\farm_health_index.py"



@'
from dataclasses import dataclass


@dataclass
class CommandStatus:

    status: str

    reason: str

    priority: str
'@ | Set-Content `
"dairyos\herd\dashboard\models\command_status.py"



@'
from ..models.farm_health_index import FarmHealthIndex
from ..models.command_status import CommandStatus


class CommandCenterIntelligenceService:


    def calculate_health_index(

        self,

        production_score,

        health_score,

        reproduction_score,

        financial_score

    ):


        total = round(

            (

                production_score * 0.40

                +

                health_score * 0.25

                +

                reproduction_score * 0.20

                +

                financial_score * 0.15

            )

        )


        return FarmHealthIndex(

            production_score,

            health_score,

            reproduction_score,

            financial_score,

            total

        )



    def evaluate_status(

        self,

        health_index,

        risk_level

    ):


        if risk_level == "HIGH" or health_index.overall_score < 60:

            return CommandStatus(

                "RED",

                "Critical operational attention required",

                "HIGH"

            )


        if risk_level == "MEDIUM" or health_index.overall_score < 80:

            return CommandStatus(

                "YELLOW",

                "Monitor operational performance",

                "MEDIUM"

            )


        return CommandStatus(

            "GREEN",

            "Operations performing normally",

            "LOW"

        )
'@ | Set-Content `
"dairyos\herd\dashboard\services\command_center_intelligence_service.py"



@'
from dairyos.herd.dashboard.services.command_center_intelligence_service import CommandCenterIntelligenceService



def test_health_index_calculation():

    result = CommandCenterIntelligenceService().calculate_health_index(

        100,

        100,

        100,

        100

    )

    assert result.overall_score == 100



def test_health_index_weighting():

    result = CommandCenterIntelligenceService().calculate_health_index(

        50,

        100,

        100,

        100

    )

    assert result.overall_score == 80



def test_green_status():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(100,100,100,100)

    status = service.evaluate_status(index,"LOW")

    assert status.status == "GREEN"



def test_yellow_status():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(80,80,80,80)

    status = service.evaluate_status(index,"MEDIUM")

    assert status.status == "YELLOW"



def test_red_status():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(50,50,50,50)

    status = service.evaluate_status(index,"HIGH")

    assert status.status == "RED"



def test_status_priority():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(50,50,50,50)

    status = service.evaluate_status(index,"HIGH")

    assert status.priority == "HIGH"



def test_status_reason():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(100,100,100,100)

    status = service.evaluate_status(index,"LOW")

    assert len(status.reason) > 0



def test_index_model():

    result = CommandCenterIntelligenceService().calculate_health_index(

        90,90,90,90

    )

    assert result.production_score == 90



def test_medium_risk():

    service = CommandCenterIntelligenceService()

    index = service.calculate_health_index(100,100,100,100)

    status = service.evaluate_status(index,"MEDIUM")

    assert status.status == "YELLOW"
'@ | Set-Content `
"tests\core\test_farm_command_center_intelligence.py"


Write-Host "HERD-027 Farm Command Center Intelligence Enhancement Build Complete"