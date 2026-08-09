from dairyos.intelligence.integration.cross_intelligence_gateway import (
    CrossIntelligenceGateway,
)

from dairyos.intelligence.integration.intelligence_pipeline import (
    IntelligencePipeline,
)


def test_cross_intelligence_gateway_creation():

    gateway = CrossIntelligenceGateway()

    assert gateway is not None


def test_intelligence_pipeline_creation():

    pipeline = IntelligencePipeline()

    assert pipeline is not None


def test_intelligence_modules_are_importable():

    from dairyos.intelligence import decision
    from dairyos.intelligence import execution
    from dairyos.intelligence import workflow
    from dairyos.intelligence import learning
    from dairyos.intelligence import memory
    from dairyos.intelligence import knowledge

    assert decision is not None
    assert execution is not None
    assert workflow is not None
    assert learning is not None
    assert memory is not None
    assert knowledge is not None


def test_command_layer_is_integrated():

    from dairyos.intelligence.command.gateway.command_gateway import (
        CommandGateway,
    )

    gateway = CommandGateway()

    assert gateway is not None


def test_decision_layer_is_integrated():

    from dairyos.intelligence.decision.gateway.decision_gateway import (
        DecisionGateway,
    )

    gateway = DecisionGateway()

    assert gateway is not None