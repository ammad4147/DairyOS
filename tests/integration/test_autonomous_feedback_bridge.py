from dairyos.intelligence.integration.autonomous_feedback_bridge import (
    AutonomousFeedbackBridge,
)


def test_autonomous_feedback_bridge_processes_cycle():

    bridge = AutonomousFeedbackBridge()


    result = {
        "decision": {
            "action": "review",
        },
        "execution": {
            "status": "completed",
        },
        "runtime": {
            "status": "completed",
            "stages": [
                "prediction",
                "decision",
                "execution",
            ],
        },
    }


    feedback = bridge.create_feedback(
        result
    )


    assert feedback["workflow"] == (
        "autonomous_intelligence"
    )

    assert feedback["success"] is True
