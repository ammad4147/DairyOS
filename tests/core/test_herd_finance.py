from datetime import date


from dairyos.herd.finance.models import (

    AnimalCost,

    MilkRevenue

)


from dairyos.herd.finance.services.finance_service import (

    FinanceService

)



def test_animal_cost_calculation():


    cost = AnimalCost(

        animal_id="HF-8001",

        cost_date=date.today(),

        feed_cost=2500,

        health_cost=100,

        breeding_cost=50

    )


    assert cost.total_cost == 2650



def test_milk_revenue_calculation():


    revenue = MilkRevenue(

        animal_id="HF-8001",

        revenue_date=date.today(),

        litres=25,

        price_per_litre=225

    )


    assert revenue.total_revenue == 5625



def test_finance_service():


    service = FinanceService()


    service.record_cost(

        AnimalCost(

            animal_id="HF-8002",

            cost_date=date.today(),

            feed_cost=2000,

            health_cost=100,

            breeding_cost=0

        )

    )


    assert service.cost_count() == 1
