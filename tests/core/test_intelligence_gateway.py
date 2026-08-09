from dairyos.intelligence.kernel.context.intelligence_context import (
    IntelligenceContext,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.interface.intelligence_gateway import (
    IntelligenceGateway,
)


def test_intelligence_gateway_processes_external_request():

    context = IntelligenceContext()


    context.add_signal(
        IntelligenceSignal(
            source="health",
            category="animal_health",
            message="Critical temperature alert",
            severity="critical",
        )
    )


    gateway = IntelligenceGateway()


    result = gateway.process(
        context
    )


    assert "assessment" in result
    assert "priorities" in result
    assert "recommendations" in result
    assert "decisions" in result


    assert (
        result["priorities"][0]["priority"]
        ==
        "immediate"
    )


    assert (
        result["decisions"][0]["priority"]
        ==
        "immediate"
    )
