$root = "C:\DairyOS"

Write-Host "Starting HERD-015 Herd Command Intelligence Build..." -ForegroundColor Cyan


# Create required directories

$directories = @(
    "dairyos\herd\dashboard\models",
    "dairyos\herd\dashboard\services",
    "tests\core"
)

foreach ($dir in $directories) {

    $path = Join-Path $root $dir

    if (!(Test-Path $path)) {

        New-Item -ItemType Directory -Path $path -Force | Out-Null

    }

}


# Create HerdCommand model

@'
from dataclasses import dataclass


@dataclass
class HerdCommand:


    farm_name: str

    total_animals: int

    production_status: str

    health_status: str

    reproduction_status: str

    financial_status: str

    overall_risk: str

    owner_attention: str
'@ | Set-Content `
"$root\dairyos\herd\dashboard\models\herd_command.py"



# Create HerdCommand service

@'
from ..models.herd_command import HerdCommand



class HerdCommandService:



    def generate(

        self,

        farm_name,

        total_animals,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False,

        production_status="STABLE",

        financial_status="POSITIVE"

    ):


        health_status = "NORMAL"

        reproduction_status = "NORMAL"

        risk = "LOW"

        attention = "No immediate action required"



        if health_alerts > 0:

            health_status = "ATTENTION REQUIRED"

            risk = "MEDIUM"

            attention = "Review animal health alerts"



        if open_cows > 3:

            reproduction_status = "MONITOR"

            if risk == "LOW":

                risk = "MEDIUM"

                attention = "Review reproductive performance"



        if replacement_shortage:

            risk = "HIGH"

            attention = "Review replacement pipeline"



        return HerdCommand(

            farm_name=farm_name,

            total_animals=total_animals,

            production_status=production_status,

            health_status=health_status,

            reproduction_status=reproduction_status,

            financial_status=financial_status,

            overall_risk=risk,

            owner_attention=attention

        )
'@ | Set-Content `
"$root\dairyos\herd\dashboard\services\herd_command_service.py"



# Create HERD-015 tests

@'
from dairyos.herd.dashboard.services.herd_command_service import HerdCommandService



def test_command_creation():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100

    )


    assert result.farm_name == "Trident Dairies"

    assert result.total_animals == 100



def test_stable_herd_status():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100

    )


    assert result.overall_risk == "LOW"



def test_health_warning():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100,

        health_alerts=2

    )


    assert result.health_status == "ATTENTION REQUIRED"

    assert result.overall_risk == "MEDIUM"



def test_reproduction_warning():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100,

        open_cows=5

    )


    assert result.reproduction_status == "MONITOR"



def test_replacement_shortage():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100,

        replacement_shortage=True

    )


    assert result.overall_risk == "HIGH"



def test_owner_attention():

    service = HerdCommandService()

    result = service.generate(

        farm_name="Trident Dairies",

        total_animals=100,

        health_alerts=1

    )


    assert "health" in result.owner_attention.lower()
'@ | Set-Content `
"$root\tests\core\test_herd_command.py"



Write-Host ""
Write-Host "HERD-015 Build Completed Successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Run validation:"
Write-Host "pytest tests/core/test_herd_command.py -v"