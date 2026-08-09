from dairyos.platform.digital_twin.services.digital_twin_service import (
    DigitalTwinService,
)


from dairyos.platform.digital_twin.simulation.models.scenario import (
    Scenario,
)



def test_complete_digital_twin_flow():


    service = DigitalTwinService()



    scenario = Scenario(

        name="milk price reduction",

        parameter="milk_price",

        change_percent=-10,

    )



    dashboard = service.process(

        farm_id="trident",

        state={

            "milking_cows":25,

            "milk_daily":625

        },

        metric="milk",

        current_value=625,

        scenario=scenario,

    )



    assert dashboard.farm_id == "trident"


    assert dashboard.current_state["milk_daily"] == 625


    assert len(dashboard.decision_signals) == 1

