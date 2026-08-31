from dairyos.platform.digital_twin.synchronization.services.digital_twin_sync_service import (
    DigitalTwinSyncService,
)
from dairyos.platform.digital_twin.persistence.repositories.digital_twin_repository import (
    DigitalTwinRepository,
)
from dairyos.platform.digital_twin.forecasting.services.forecast_engine import (
    ForecastEngine,
)
from dairyos.platform.digital_twin.decision.services.decision_bridge import (
    DecisionBridge,
)
from dairyos.platform.digital_twin.presentation.services.dashboard_adapter import (
    DashboardAdapter,
)


class DigitalTwinService:
    """Enterprise Digital Twin orchestration service.

    The Digital Twin provides forecast and explicit what-if projections over
    persisted operational facts. It never writes projections back as farm
    facts, and all what-if assumptions are explicit inputs.
    """

    def __init__(
        self,
        *,
        repository=None,
        forecaster=None,
        decision=None,
        dashboard=None,
        sync=None,
    ):
        self.sync = sync or DigitalTwinSyncService()
        self.repository = repository or DigitalTwinRepository()
        self.forecaster = forecaster or ForecastEngine()
        self.decision = decision or DecisionBridge()
        self.dashboard = dashboard or DashboardAdapter()

    @staticmethod
    def _scenario_projection(current_value, change_percent):
        impact = current_value * change_percent / 100.0
        projected = current_value + impact

        severity = "low"
        if abs(change_percent) > 10:
            severity = "medium"
        if abs(change_percent) > 25:
            severity = "high"

        return {
            "scenario_change_percent": change_percent,
            "projected_value": projected,
            "variance": impact,
            "risk_level": severity,
        }

    def process(
        self,
        farm_id,
        state,
        metric,
        current_value,
        scenario_name,
        parameter,
        change_percent,
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

        projection = self._scenario_projection(
            current_value=current_value,
            change_percent=change_percent,
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
            scenarios={
                "name": scenario_name,
                "parameter": parameter,
                "change_percent": projection["scenario_change_percent"],
                "projected_value": projection["projected_value"],
                "variance": projection["variance"],
                "risk_level": projection["risk_level"],
            },
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
        return self.process(
            farm_id=farm_id,
            state=state or {},
            metric=metric,
            current_value=current_value,
            scenario_name=scenario_name,
            parameter=parameter,
            change_percent=change_percent,
            growth_rate=growth_rate_percent / 100.0,
            horizon_days=horizon_days,
        )
