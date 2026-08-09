$root = "C:\DairyOS"

Write-Host "Starting HERD-017 Domain Service Intelligence Wiring Build..." -ForegroundColor Cyan


# Ensure directories exist

$directories = @(
    "dairyos\herd\intelligence\models",
    "dairyos\herd\intelligence\services",
    "tests\core"
)

foreach ($dir in $directories) {

    $path = Join-Path $root $dir

    if (!(Test-Path $path)) {

        New-Item -ItemType Directory -Path $path -Force | Out-Null

    }
}



# Create Domain Snapshot model

@'
from dataclasses import dataclass



@dataclass
class DomainSnapshot:


    health_events: int = 0

    vaccinations: int = 0

    milk_records: int = 0

    production_groups: int = 0

    feed_plans: int = 0

    consumptions: int = 0

    pregnancies: int = 0

    costs: int = 0

    revenues: int = 0
'@ | Set-Content `
"$root\dairyos\herd\intelligence\models\domain_snapshot.py"



# Create Domain Intelligence Adapter

@'
from ..models.domain_snapshot import DomainSnapshot



class DomainIntelligenceAdapter:



    def collect(

        self,

        health_service,

        production_service,

        nutrition_service,

        reproduction_service,

        finance_service

    ):


        return DomainSnapshot(

            health_events=health_service.health_event_count(),

            vaccinations=health_service.vaccination_count(),

            milk_records=production_service.milk_record_count(),

            production_groups=production_service.group_count(),

            feed_plans=nutrition_service.feed_plan_count(),

            consumptions=nutrition_service.consumption_count(),

            pregnancies=reproduction_service.pregnancy_count(),

            costs=finance_service.cost_count(),

            revenues=finance_service.revenue_count()

        )
'@ | Set-Content `
"$root\dairyos\herd\intelligence\services\domain_adapter.py"



# Extend Herd Aggregator

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



    def from_snapshot(

        self,

        snapshot,

        farm_name,

        total_animals

    ):


        financial_status = "POSITIVE"


        if snapshot.costs > 0 and snapshot.revenues == 0:

            financial_status = "WARNING"



        feed_status = "NORMAL"


        if snapshot.feed_plans == 0:

            feed_status = "UNKNOWN"



        return HerdContext(

            farm_name=farm_name,

            total_animals=total_animals,

            health_alerts=snapshot.health_events,

            production_status=(

                "ACTIVE"

                if snapshot.milk_records > 0

                else "INACTIVE"

            ),

            financial_status=financial_status,

            feed_status=feed_status

        )
'@ | Set-Content `
"$root\dairyos\herd\intelligence\services\herd_aggregator.py"



# Create HERD-017 tests

@'
from dairyos.herd.health.services.health_service import HealthService

from dairyos.herd.production.services.production_service import ProductionService

from dairyos.herd.nutrition.services.nutrition_service import NutritionService

from dairyos.herd.reproduction.services.reproduction_service import ReproductionService

from dairyos.herd.finance.services.finance_service import FinanceService

from dairyos.herd.intelligence.services.domain_adapter import DomainIntelligenceAdapter

from dairyos.herd.intelligence.services.herd_aggregator import HerdAggregator



def test_domain_snapshot_creation():


    snapshot = DomainIntelligenceAdapter().collect(

        HealthService(),

        ProductionService(),

        NutritionService(),

        ReproductionService(),

        FinanceService()

    )


    assert snapshot.health_events == 0



def test_health_adapter_collection():


    health = HealthService()

    health.add_health_record("case")


    snapshot = DomainIntelligenceAdapter().collect(

        health,

        ProductionService(),

        NutritionService(),

        ReproductionService(),

        FinanceService()

    )


    assert snapshot.health_events == 1



def test_production_adapter_collection():


    production = ProductionService()

    production.record_milk("milk")


    snapshot = DomainIntelligenceAdapter().collect(

        HealthService(),

        production,

        NutritionService(),

        ReproductionService(),

        FinanceService()

    )


    assert snapshot.milk_records == 1



def test_nutrition_adapter_collection():


    nutrition = NutritionService()

    nutrition.add_feed_plan("plan")


    snapshot = DomainIntelligenceAdapter().collect(

        HealthService(),

        ProductionService(),

        nutrition,

        ReproductionService(),

        FinanceService()

    )


    assert snapshot.feed_plans == 1



def test_reproduction_adapter_collection():


    reproduction = ReproductionService()

    reproduction.confirm_pregnancy("pregnancy")


    snapshot = DomainIntelligenceAdapter().collect(

        HealthService(),

        ProductionService(),

        NutritionService(),

        reproduction,

        FinanceService()

    )


    assert snapshot.pregnancies == 1



def test_finance_adapter_collection():


    finance = FinanceService()

    finance.record_cost("cost")


    snapshot = DomainIntelligenceAdapter().collect(

        HealthService(),

        ProductionService(),

        NutritionService(),

        ReproductionService(),

        finance

    )


    assert snapshot.costs == 1



def test_full_domain_to_context_flow():


    snapshot = DomainIntelligenceAdapter().collect(

        HealthService(),

        ProductionService(),

        NutritionService(),

        ReproductionService(),

        FinanceService()

    )


    context = HerdAggregator().from_snapshot(

        snapshot,

        "Trident Dairies",

        100

    )


    assert context.farm_name == "Trident Dairies"

    assert context.total_animals == 100
'@ | Set-Content `
"$root\tests\core\test_herd_domain_intelligence.py"



Write-Host ""
Write-Host "HERD-017 Build Completed Successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Validation commands:"
Write-Host "pytest tests/core/test_herd_domain_intelligence.py -v"
Write-Host "pytest -q"