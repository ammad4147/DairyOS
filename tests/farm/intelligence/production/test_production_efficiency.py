from dairyos.farm.intelligence.production.services.production_efficiency_service import (
    ProductionEfficiencyService,
)



def test_production_efficiency_calculation():


    result = ProductionEfficiencyService().evaluate(

        milk_litres=600,

        milking_animals=25,

        feed_cost=60000,

    )


    assert (
        result.litres_per_animal
        == 24
    )


    assert (
        result.feed_cost_per_litre
        == 100
    )


    assert (
        result.efficiency_status
        == "normal"
    )
