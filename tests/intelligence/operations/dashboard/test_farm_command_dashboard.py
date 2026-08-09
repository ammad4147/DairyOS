from dairyos.intelligence.operations.dashboard.farm_command_dashboard import (
    FarmCommandDashboard,
)


from dairyos.intelligence.operations.models.farm_situation import (
    FarmSituation,
)



def test_dashboard_builds_operational_view():


    dashboard = FarmCommandDashboard()



    situation = FarmSituation(

        total_animals=50,

        milking_cows=25,

        dry_cows=10,

        close_up_cows=3,

        animals_requiring_attention=2,

        daily_milk_litres=600,

        milk_change_percentage=-3,

        feed_cost_per_litre=100,

        reproduction_alerts=1,

        overall_status="attention",

    )



    result = dashboard.generate(

        situation,

        {

            "animals_requiring_attention":2

        },

        {

            "pregnant_animals":18

        },

    )



    assert result["farm_status"] == (
        "attention"
    )


    assert result["herd"]["total_animals"] == (
        50
    )


    assert result["production"]["daily_milk_litres"] == (
        600
    )
