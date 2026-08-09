from dairyos.platform.digital_twin.simulation.models.simulation_result import (
    SimulationResult,
)



class Simulator:
    """
    Runs digital twin what-if simulations.
    """



    def simulate(

        self,

        scenario,

        baseline_value,

    ):


        impact = (

            baseline_value *

            scenario.change_percent /

            100

        )


        simulated = (

            baseline_value +

            impact

        )


        risk = "low"



        if abs(scenario.change_percent) > 10:

            risk = "medium"



        if abs(scenario.change_percent) > 25:

            risk = "high"



        return SimulationResult(

            scenario_name=scenario.name,

            baseline_value=baseline_value,

            simulated_value=simulated,

            variance=impact,

            risk_level=risk,

        )

