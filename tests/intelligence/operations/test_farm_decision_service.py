from dairyos.intelligence.operations.services.farm_situation_service import (
    FarmSituationService,
)

from dairyos.intelligence.operations.services.farm_decision_service import (
    FarmDecisionService,
)



def test_farm_situation_creates_operational_actions():

    situation = FarmSituationService().evaluate(

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


    actions = FarmDecisionService().create_actions(
        situation
    )


    assert len(actions) == 3

    assert actions[0].action_type == (
        "animal_review"
    )

    assert actions[1].priority == (
        "high"
    )
