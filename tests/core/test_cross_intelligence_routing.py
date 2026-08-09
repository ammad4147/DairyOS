from dairyos.intelligence.integration.cross_intelligence_gateway import (
    CrossIntelligenceGateway,
)


class MockGateway:

    def __init__(self, name):

        self.name = name


    def execute(self, value):

        return self.name


    def dispatch(self, value):

        return self.name


    def evaluate(self, value):

        return self.name


    def predict(self, value):

        return self.name



def test_cross_intelligence_gateway_routing():

    gateway = CrossIntelligenceGateway(
        prediction=MockGateway("prediction"),
        decision=MockGateway("decision"),
        command=MockGateway("command"),
        execution=MockGateway("execution"),
    )


    result = gateway.process(
        {"signal": "test"}
    )


    assert result["prediction"] == "prediction"
    assert result["decision"] == "decision"
    assert result["command"] == "command"
    assert result["execution"] == "execution"
