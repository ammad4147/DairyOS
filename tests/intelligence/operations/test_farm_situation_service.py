from dairyos.intelligence.operations.services.farm_situation_service import (
    FarmSituationService,
)



def test_farm_situation_detects_attention_condition():

    service = FarmSituationService()


    situation = service.evaluate(

        total_animals=30,

        milking_cows=20,

        dry_cows=5,

        close_up_cows=2,

        animals_requiring_attention=3,

        daily_milk_litres=580,

        previous_day_milk_litres=620,

        feed_cost_per_litre=95,

        reproduction_alerts=1,
    )


    assert situation.overall_status == "ATTENTION"

    assert situation.animals_requiring_attention == 3

    assert situation.milk_change_percentage < -5
