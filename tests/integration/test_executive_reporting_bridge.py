from dairyos.intelligence.integration.executive_reporting_bridge import (
    ExecutiveReportingBridge,
)

from dairyos.herd.dashboard.models.executive_cockpit import (
    ExecutiveCockpit,
)



def test_executive_reporting_bridge_builds_report():


    cockpit = ExecutiveCockpit(

        farm_name="Trident Dairies",

        overall_score=80,

        health_score=85,

        production_score=75,

        reproduction_score=70,

        financial_score=90,

        risk_level="normal",

        priority="monitor",

        summary="Stable operations",

        actions=[
            "Continue monitoring"
        ],

        alerts=[],
    )


    bridge = ExecutiveReportingBridge()


    report = bridge.build_report(
        cockpit
    )


    assert report.farm_name == "Trident Dairies"

    assert report.management_effectiveness == 80

    assert report.pending_actions == 1
