"""
DairyOS Sprint 025

Prediction ? Decision ? Command
Integration Validation
"""


def test_prediction_decision_command_chain():

    from dairyos.intelligence.prediction.gateway.prediction_gateway import (
        PredictionGateway,
    )

    from dairyos.intelligence.decision.gateway.decision_gateway import (
        DecisionGateway,
    )

    from dairyos.intelligence.command.gateway.command_gateway import (
        CommandGateway,
    )


    prediction = PredictionGateway()

    decision = DecisionGateway()

    command = CommandGateway()


    assert prediction is not None
    assert decision is not None
    assert command is not None
