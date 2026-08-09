from dairyos.intelligence.operations.services.farm_situation_service import (
    FarmSituationService,
)

from dairyos.intelligence.operations.health.services.farm_health_service import (
    FarmHealthService,
)



def test_farm_health_detects_operational_risk():


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


    assert report.overall_status == (
        "ATTENTION"
    )

    assert report.risk_level == (
        "HIGH"
    )

    assert len(
        report.recommended_actions
    ) > 0
