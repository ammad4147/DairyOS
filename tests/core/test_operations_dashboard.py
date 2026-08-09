from dairyos.operations.dashboard.services.dashboard_builder_service import (
    DashboardBuilderService,
)

from dairyos.operations.dashboard.services.dashboard_summary_service import (
    DashboardSummaryService,
)



def test_dashboard_health_green():

    service = DashboardBuilderService()


    dashboard = service.build(
        dashboard_id="DASH-001",
        open_issue_count=2,
        resolution_rate=95,
        effectiveness_score=90,
    )


    assert dashboard.operational_health == "GREEN"



def test_dashboard_summary():

    builder = DashboardBuilderService()

    dashboard = builder.build(
        dashboard_id="DASH-002",
        open_issue_count=5,
        resolution_rate=80,
        effectiveness_score=75,
    )


    service = DashboardSummaryService()


    summary = service.summarize(dashboard)


    assert summary["health"] == "AMBER"
