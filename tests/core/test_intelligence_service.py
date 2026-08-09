from dairyos.intelligence.services.intelligence_service import (
    IntelligenceService,
)

from dairyos.intelligence.kernel.models.intelligence_signal import (
    IntelligenceSignal,
)


def test_intelligence_service_submits_and_processes_signal():

    service = IntelligenceService()


    service.submit_signal(
        IntelligenceSignal(
            source="health",
            category="animal_health",
            message="Critical temperature alert",
            severity="critical",
        )
    )


    result = service.process()


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
