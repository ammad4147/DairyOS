from datetime import datetime


from dairyos.operations.alerts.models.alert_severity import (
    AlertSeverity,
)

from dairyos.operations.alerts.models.operational_alert import (
    OperationalAlert,
)

from dairyos.operations.alerts.services.alert_management_service import (
    AlertManagementService,
)

from dairyos.operations.alerts.services.alert_resolution_service import (
    AlertResolutionService,
)



def test_create_operational_alert():

    service = AlertManagementService()


    alert = OperationalAlert(
        alert_id="ALT-001",
        title="Feed Delay",
        severity=AlertSeverity.CRITICAL,
        description="Feeding task delayed",
        created_at=datetime.now(),
    )


    service.create_alert(alert)


    assert len(service.active_alerts()) == 1



def test_resolve_operational_alert():

    management = AlertManagementService()
    resolution = AlertResolutionService()


    alert = OperationalAlert(
        alert_id="ALT-002",
        title="Task Completed",
        severity=AlertSeverity.INFO,
        description="Issue resolved",
        created_at=datetime.now(),
    )


    management.create_alert(alert)

    resolution.resolve(alert)


    assert alert.resolved is True
