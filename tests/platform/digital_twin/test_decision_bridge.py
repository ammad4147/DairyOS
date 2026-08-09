from dairyos.platform.digital_twin.decision.services.decision_bridge import (
    DecisionBridge,
)



def test_digital_twin_decision_signal():


    bridge = DecisionBridge()



    signal = bridge.create_signal(

        metric="feed_cost",

        forecast_change=12,

        confidence=0.82,

    )



    assert signal.source == "digital_twin"


    assert signal.severity == "medium"


    assert signal.confidence == 0.82

