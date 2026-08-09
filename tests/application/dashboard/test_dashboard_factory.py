from dairyos.app import container
from dairyos.application.dashboard.dashboard_factory import (
    DashboardFactory,
)


def test_dashboard_factory_creates_service():

    dashboard = (
        DashboardFactory.create(
            container.runtime
        )
    )

    snapshot = (
        dashboard.get_today()
    )

    assert snapshot is not None
    assert snapshot.milk_total_litres == 0
