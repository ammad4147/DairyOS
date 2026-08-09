from dairyos.intelligence.operations.services.farm_situation_service import (
    FarmSituationService,
)

from dairyos.intelligence.operations.health.services.farm_health_service import (
    FarmHealthService,
)

from dairyos.intelligence.operations.health.services.health_action_service import (
    HealthActionService,
)



def test_health_report_creates_farm_actions():


    situation = FarmSituationService().evaluate(

        total_animals=50,

        milking_cows=25,

        dry_cows=10,

        close_up_cows=3,

        animals_requiring_attention=2,

        daily_milk_litres=560,

        previous_day_milk_litres=620,

        feed_cost_per_litre=100,

        reproduction_alerts=1,
    )


    report = FarmHealthService().evaluate(
        situation
    )


    actions = HealthActionService().create_actions(
        report
    )


    assert len(actions) > 0

    assert actions[0].action_type == (
        "farm_health_review"
    )

    assert actions[0].priority == (
        "high"
    )
