from dairyos.intelligence.integration.intelligence_dashboard_bridge import (
    IntelligenceDashboardBridge,
)


def test_intelligence_dashboard_bridge_summary():

    bridge = IntelligenceDashboardBridge()


    result = {

        "runtime": {

            "cycle_id": "cycle-001",

            "status": "completed",

            "stage_count": 2,

            "stages": [

                "prediction",

                "decision",

            ],

        }

    }


    summary = bridge.build_summary(
        result
    )


    assert summary["status"] == "completed"

    assert summary["stage_count"] == 2

    assert "prediction" in summary["stages"]