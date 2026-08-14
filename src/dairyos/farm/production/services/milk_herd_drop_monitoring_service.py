from __future__ import annotations

from datetime import date

from dairyos.data.repositories.repository_factory import RepositoryFactory
from dairyos.farm.findings.services.operational_finding_service import OperationalFindingService
from dairyos.farm.operations.services.milk_production_trend_intelligence_service import MilkProductionTrendIntelligenceService


class MilkHerdDailyDropMonitoringService:
    """Raises one farm-level milk decline finding from complete dated totals."""

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

        severity = "HIGH" if percentage >= -20 else "CRITICAL"
        rf = RepositoryFactory.create()
        try:
            OperationalFindingService(rf.operational_findings()).raise_or_update(
                source_module="MILK",
                severity=severity,
                title=f"Farm milk yield declined on {production_date.isoformat()}",
                detail=(
                    f"{result['last_date']}: {result['last_date_total_litres']:.1f} L -> "
                    f"{result['reference_date']}: {result['current_total_litres']:.1f} L "
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
