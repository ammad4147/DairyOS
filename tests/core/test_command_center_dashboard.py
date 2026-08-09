from dairyos.herd.dashboard.services.command_center_dashboard_service import CommandCenterDashboardService
from dairyos.herd.dashboard.services.executive_reporting_service import ExecutiveReportingService



def create_report():

    return ExecutiveReportingService().generate(

        "Trident Dairies",

        95,

        90,

        88,

        92,

        3,

        85,

        "Review replacement pipeline"

    )



def test_dashboard_creation():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.farm_name == "Trident Dairies"



def test_dashboard_status():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.farm_status == "GREEN"



def test_health_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.health_score == 95



def test_action_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.pending_actions == 3



def test_recommendation_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report(),

        recommendations_count=5

    )

    assert dashboard.recommendations_count == 5



def test_history_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report(),

        historical_actions=20

    )

    assert dashboard.historical_actions == 20



def test_effectiveness_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.effectiveness_score == 85



def test_priority_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.priority_message == "Review replacement pipeline"



def test_finance_visibility():

    dashboard = CommandCenterDashboardService().generate(

        create_report()

    )

    assert dashboard.financial_score == 92



def test_complete_dashboard_payload():

    dashboard = CommandCenterDashboardService().generate(

        create_report(),

        recommendations_count=4,

        historical_actions=15

    )

    assert dashboard.historical_actions == 15
