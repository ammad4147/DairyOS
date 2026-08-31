from dairyos.platform.digital_twin.presentation.models.digital_twin_dashboard import (
    DigitalTwinDashboard,
)


class DashboardAdapter:
    """
    Converts Digital Twin forecasts and explicit what-if projections
    into the existing presentation model.
    """

    def build(
        self,
        farm_id,
        current_state,
        forecasts,
        scenarios,
        signals,
    ):
        return DigitalTwinDashboard(
            farm_id=farm_id,
            current_state=current_state,
            forecast_summary=forecasts,
            scenario_summary=scenarios,
            decision_signals=signals,
        )
