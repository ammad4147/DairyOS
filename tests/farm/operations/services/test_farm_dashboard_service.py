from dairyos.farm.operations.services import (
    FarmDashboardService,
)



def test_dashboard_builds_operational_view():

    dashboard = FarmDashboardService()


    result = dashboard.build_dashboard()


    assert "milk_today" in result

    assert "feed_quantity_today" in result

    assert "health_alerts" in result
