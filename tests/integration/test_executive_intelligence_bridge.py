from dairyos.intelligence.integration.executive_intelligence_bridge import (
    ExecutiveIntelligenceBridge,
)


def test_executive_intelligence_bridge_summary():

    bridge = ExecutiveIntelligenceBridge()


    summary = bridge.build_summary(
        {
            "status": "completed",
            "stages": [
                "prediction",
            ],
            "governance": {
                "approved": False,
                "reason": "Review required",
            },
        }
    )


    assert summary.farm_status == "completed"

    assert summary.top_concern == "Review required"

    assert summary.recommended_focus == "prediction"

    assert summary.owner_attention is True



def test_executive_intelligence_bridge_command_center():

    bridge = ExecutiveIntelligenceBridge()


    summary = bridge.build_summary(
        {
            "status": "completed",
            "stages": [],
            "governance": None,
        }
    )


    cockpit = bridge.build_cockpit(
        summary
    )


    command = bridge.build_command_center(
        cockpit
    )


    assert cockpit.farm_name == "Trident Dairies"

    assert command.farm_name == "Trident Dairies"

    assert command.time_horizon == "current_cycle"
