from dairyos.intelligence.kernel.context.intelligence_context import (
    IntelligenceContext,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)

from dairyos.intelligence.kernel.orchestration.intelligence_orchestrator import (
    IntelligenceOrchestrator,
)


def test_intelligence_orchestrator_processes_complete_pipeline():

    context = IntelligenceContext()


    context.add_signal(
        IntelligenceSignal(
            source="health",
            category="animal_health",
            message="Critical temperature alert",
            severity="critical",
        )
    )


    orchestrator = IntelligenceOrchestrator()


    result = orchestrator.process(
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
        result["recommendations"][0]["recommendation"]
        ==
        "Immediate inspection required"
    )


    assert (
        result["decisions"][0]["priority"]
        ==
        "immediate"
    )
