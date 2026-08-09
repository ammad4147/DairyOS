from dairyos.platform.digital_twin.services.digital_twin_service import (
    DigitalTwinService,
)


from dairyos.platform.digital_twin.simulation.models.scenario import (
    Scenario,
)



def test_enterprise_digital_twin_service():


    service = DigitalTwinService()



    scenario = Scenario(

        name="feed increase",

        parameter="feed",

        change_percent=10,

    )



    dashboard = service.process(

        farm_id="farm001",

        state={

            "animals":50

        },

        metric="milk",

        current_value=625,

        scenario=scenario,

    )



    assert dashboard.farm_id == "farm001"


    assert dashboard.current_state["animals"] == 50


    assert len(dashboard.decision_signals) == 1

