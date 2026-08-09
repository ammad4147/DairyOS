from dairyos.platform.digital_twin.presentation.models.digital_twin_dashboard import (
    DigitalTwinDashboard,
)



class DashboardAdapter:
    """
    Converts digital twin intelligence
    into Command Center format.
    """



    def build(

        self,

        farm_id,

        current_state,

        forecasts,

        simulations,

        signals,

    ):


        return DigitalTwinDashboard(

            farm_id=farm_id,

            current_state=current_state,

            forecast_summary=forecasts,

            simulation_summary=simulations,

            decision_signals=signals,

        )

