from dairyos.platform.digital_twin.synchronization.services.digital_twin_sync_service import DigitalTwinSyncService
from dairyos.platform.digital_twin.persistence.repositories.digital_twin_repository import DigitalTwinRepository
from dairyos.platform.digital_twin.forecasting.services.forecast_engine import ForecastEngine
from dairyos.platform.digital_twin.simulation.services.simulator import Simulator
from dairyos.platform.digital_twin.decision.services.decision_bridge import DecisionBridge
from dairyos.platform.digital_twin.presentation.services.dashboard_adapter import DashboardAdapter
from dairyos.platform.digital_twin.simulation.models.scenario import Scenario


class DigitalTwinService:
    """Enterprise Digital Twin orchestration service.

    The Digital Twin is a scenario/forecast projection over persisted facts.
    It never fabricates farm facts and all forecast/scenario assumptions are
    explicit inputs to this service.
    """

    def __init__(self, *, repository=None, forecaster=None, simulator=None, decision=None, dashboard=None, sync=None):
        self.sync = sync or DigitalTwinSyncService()
        self.repository = repository or DigitalTwinRepository()
        self.forecaster = forecaster or ForecastEngine()
        self.simulator = simulator or Simulator()
        self.decision = decision or DecisionBridge()
        self.dashboard = dashboard or DashboardAdapter()

    def process(
        self,
        farm_id,
        state,
        metric,
        current_value,
        scenario,
        *,
        growth_rate=0.0,
        horizon_days=30,
    ):
        if horizon_days <= 0:
            raise ValueError("horizon_days must be greater than zero")

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
            growth_rate=growth_rate,
            horizon_days=horizon_days,
        )
        simulation = self.simulator.simulate(
            scenario=scenario,
            baseline_value=current_value,
        )

        forecast_change = (
            ((forecast.predicted_value - current_value) / current_value) * 100
            if current_value
            else 0.0
        )
        signal = self.decision.create_signal(
            metric=metric,
            forecast_change=round(forecast_change, 4),
            confidence=forecast.confidence,
        )

        return self.dashboard.build(
            farm_id=farm_id,
            current_state=state,
            forecasts={"metric": forecast.predicted_value},
            simulations={"risk": simulation.risk_level},
            signals=[signal],
        )

    def scenario(
        self,
        *,
        farm_id,
        metric,
        current_value,
        scenario_name,
        parameter,
        change_percent,
        growth_rate_percent=0.0,
        horizon_days=30,
        state=None,
    ):
        scenario = Scenario(
            name=scenario_name,
            parameter=parameter,
            change_percent=change_percent,
        )
        return self.process(
            farm_id=farm_id,
            state=state or {},
            metric=metric,
            current_value=current_value,
            scenario=scenario,
            growth_rate=growth_rate_percent / 100.0,
            horizon_days=horizon_days,
        )
