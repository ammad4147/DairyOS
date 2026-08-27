from __future__ import annotations

from collections.abc import Callable
from datetime import date

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import (
    MilkProductionTrendIntelligenceService,
)
from dairyos.farm.production.services.milk_finding_service import MilkFindingService
from dairyos.farm.settings.services.deployment_control_service import DeploymentControlService
from dairyos.farm.settings.services.farm_settings_service import FarmSettingsService


class MilkHerdDailyDropMonitoringService:
    """Raises one farm-level milk decline finding from complete dated totals."""

    def __init__(self, deployment_checker: Callable[[], bool] | None = None):
        self.deployment_checker = deployment_checker

    @staticmethod
    def _is_deployed(rf, checker: Callable[[], bool] | None) -> bool:
        if checker is not None:
            return bool(checker())
        app_settings = getattr(rf, "app_settings", None)
        if app_settings is None:
            return True
        return DeploymentControlService(FarmSettingsService(app_settings())).is_deployed()

    def monitor(self, production_date: date) -> dict:
        trend = MilkProductionTrendIntelligenceService().generate(
            as_of_date=production_date,
            period_days=7,
        )
        result = trend.summary()

        if result["comparison_status"] != "COMPARED":
            return result

        percentage = result["variance_percentage"]
        if percentage is None or percentage > -10:
            return result

        rf = RepositoryFactory.create()
        try:
            if not self._is_deployed(rf, self.deployment_checker):
                return {
                    **result,
                    "comparison_status": "PRE_DEPLOYMENT",
                    "operational_date": production_date.isoformat(),
                }

            severity = "HIGH" if percentage >= -20 else "CRITICAL"
            MilkFindingService(rf.operational_findings()).raise_or_update(
                severity=severity,
                title=f"Farm milk yield declined on {production_date.isoformat()}",
                detail=(
                    f"{result['prior_date']}: {result['prior_total_litres']:.1f} L -> "
                    f"{production_date.isoformat()}: {result['daily_total']:.1f} L "
                    f"({abs(percentage):.1f}% decline)."
                ),
                subject_type="FARM",
                subject_id="MILK",
                route="/farm/milk",
                dedupe_key="MILK_HERD_DAILY_DROP",
            )
        finally:
            rf.close()

        return result
