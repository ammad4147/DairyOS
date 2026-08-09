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
