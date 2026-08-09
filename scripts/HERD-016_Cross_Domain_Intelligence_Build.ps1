$root = "C:\DairyOS"

Write-Host "Starting HERD-016 Cross Domain Intelligence Aggregation Build..." -ForegroundColor Cyan


# Ensure folders exist

$directories = @(
    "dairyos\herd\intelligence\models",
    "dairyos\herd\intelligence\services",
    "dairyos\herd\dashboard\services",
    "tests\core"
)

foreach ($dir in $directories) {

    $path = Join-Path $root $dir

    if (!(Test-Path $path)) {

        New-Item -ItemType Directory -Path $path -Force | Out-Null

    }

}



# Create Herd Context model

@'
from dataclasses import dataclass



@dataclass
class HerdContext:


    farm_name: str

    total_animals: int

    health_alerts: int = 0

    open_cows: int = 0

    replacement_shortage: bool = False

    production_status: str = "STABLE"

    financial_status: str = "POSITIVE"

    feed_status: str = "NORMAL"
'@ | Set-Content `
"$root\dairyos\herd\intelligence\models\herd_context.py"



# Create Herd Aggregator service

@'
from ..models.herd_context import HerdContext



class HerdAggregator:



    def build(

        self,

        farm_name,

        total_animals,

        health_alerts=0,

        open_cows=0,

        replacement_shortage=False,

        production_status="STABLE",

        financial_status="POSITIVE",

        feed_status="NORMAL"

    ):


        return HerdContext(

            farm_name=farm_name,

            total_animals=total_animals,

            health_alerts=health_alerts,

            open_cows=open_cows,

            replacement_shortage=replacement_shortage,

            production_status=production_status,

            financial_status=financial_status,

            feed_status=feed_status

        )
'@ | Set-Content `
"$root\dairyos\herd\intelligence\services\herd_aggregator.py"



# Upgrade Herd Command Service

@'
from ..models.herd_command import HerdCommand



class HerdCommandService:



    def generate_from_context(self, context):


        return self.generate(

            farm_name=context.farm_name,

            total_animals=context.total_animals,

            health_alerts=context.health_alerts,

            open_cows=context.open_cows,

            replacement_shortage=context.replacement_shortage,

            production_status=context.production_status,

            financial_status=context.financial_status

        )



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



# Create HERD-016 tests

@'
from dairyos.herd.intelligence.services.herd_aggregator import HerdAggregator

from dairyos.herd.dashboard.services.herd_command_service import HerdCommandService



def test_context_creation():

    aggregator = HerdAggregator()

    context = aggregator.build(

        farm_name="Trident Dairies",

        total_animals=100

    )


    assert context.total_animals == 100



def test_context_to_command():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.farm_name == "Trident Dairies"



def test_health_signal_propagation():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        health_alerts=2

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.health_status == "ATTENTION REQUIRED"



def test_reproduction_signal_propagation():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        open_cows=5

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.reproduction_status == "MONITOR"



def test_production_signal():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        production_status="HIGH"

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.production_status == "HIGH"



def test_financial_signal():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        financial_status="WARNING"

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.financial_status == "WARNING"



def test_replacement_risk():

    context = HerdAggregator().build(

        farm_name="Trident Dairies",

        total_animals=100,

        replacement_shortage=True

    )


    command = HerdCommandService().generate_from_context(context)


    assert command.overall_risk == "HIGH"
'@ | Set-Content `
"$root\tests\core\test_herd_aggregation.py"



Write-Host ""
Write-Host "HERD-016 Build Completed Successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Run validation:"
Write-Host "pytest tests/core/test_herd_aggregation.py -v"