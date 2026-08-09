from dairyos.app import container
from dairyos.application.dashboard.dashboard_factory import (
    DashboardFactory,
)


def test_dashboard_factory_exposes_command_center_snapshot():

    dashboard = (
        DashboardFactory.create(
            container.runtime
        )
    )

    snapshot = (
        dashboard
        .get_command_center_snapshot()
    )

    assert snapshot is not None

    assert snapshot["system"] == "DairyOS"

    assert (
        "command_center"
        in snapshot
    )
