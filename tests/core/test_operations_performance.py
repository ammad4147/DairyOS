from dairyos.operations.performance.models.operational_kpi import OperationalKPI
from dairyos.operations.performance.services.kpi_service import KPIService

from dairyos.operations.performance.models.performance_measurement import (
    PerformanceMeasurement,
)

from dairyos.operations.performance.services.performance_service import (
    PerformanceService,
)


def test_kpi_registration():

    service = KPIService()

    service.register_kpi(
        OperationalKPI(
            kpi_id="KPI-001",
            name="Milk Production",
            category="Production",
            target_value=600,
            unit="Litres",
        )
    )

    assert len(service.get_kpis()) == 1


def test_measurement_record():

    service = PerformanceService()

    service.record_measurement(
        PerformanceMeasurement(
            measurement_id="M-001",
            kpi_id="KPI-001",
            actual_value=620,
            period="Daily",
        )
    )

    assert service.get_measurements()[0].actual_value == 620
