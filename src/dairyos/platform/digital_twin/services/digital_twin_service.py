from dairyos.platform.digital_twin.synchronization.services.digital_twin_sync_service import (
    DigitalTwinSyncService,
)


from dairyos.platform.digital_twin.persistence.repositories.digital_twin_repository import (
    DigitalTwinRepository,
)


from dairyos.platform.digital_twin.forecasting.services.forecast_engine import (
    ForecastEngine,
)


from dairyos.platform.digital_twin.simulation.services.simulator import (
    Simulator,
)


from dairyos.platform.digital_twin.decision.services.decision_bridge import (
    DecisionBridge,
)


from dairyos.platform.digital_twin.presentation.services.dashboard_adapter import (
    DashboardAdapter,
)



class DigitalTwinService:
    """
    Enterprise Digital Twin orchestration service.
    """



    def __init__(self):

        self.sync = DigitalTwinSyncService()

        self.repository = DigitalTwinRepository()

        self.forecaster = ForecastEngine()

        self.simulator = Simulator()

        self.decision = DecisionBridge()

        self.dashboard = DashboardAdapter()



    def process(

        self,

        farm_id,

        state,

        metric,

        current_value,

        scenario,

    ):


        self.sync.synchronize(

            source="farm_operations",

            event_type="state_update",

            entity_id=farm_id,

            payload=state,

        )



        self.repository.save(

            farm_id=farm_id,

            state=state,

            snapshot_type="operational",

        )



        forecast = self.forecaster.forecast(

            metric=metric,

            current_value=current_value,

            growth_rate=0.05,

            horizon_days=30,

        )



        simulation = self.simulator.simulate(

            scenario=scenario,

            baseline_value=current_value,

        )



        signal = self.decision.create_signal(

            metric=metric,

            forecast_change=5,

            confidence=forecast.confidence,

        )



        dashboard = self.dashboard.build(

            farm_id=farm_id,

            current_state=state,

            forecasts={

                "metric":

                forecast.predicted_value

            },

            simulations={

                "risk":

                simulation.risk_level

            },

            signals=[signal],

        )


        return dashboard

