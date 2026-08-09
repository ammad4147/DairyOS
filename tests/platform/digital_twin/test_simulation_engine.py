from dairyos.platform.digital_twin.simulation.models.scenario import (
    Scenario,
)


from dairyos.platform.digital_twin.simulation.services.simulator import (
    Simulator,
)



def test_scenario_simulation():


    simulator = Simulator()



    scenario = Scenario(

        name="Feed cost increase",

        parameter="feed_cost",

        change_percent=15,

    )



    result = simulator.simulate(

        scenario,

        100000,

    )



    assert result.simulated_value == 115000


    assert result.risk_level == "medium"

