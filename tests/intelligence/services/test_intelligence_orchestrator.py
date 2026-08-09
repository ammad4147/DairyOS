from dairyos.intelligence.services.intelligence_orchestrator import (
    IntelligenceOrchestrator,
)


def test_intelligence_orchestrator_returns_pipeline_result():

    service = IntelligenceOrchestrator()


    result = service.evaluate(
        {}
    )


    assert "signals" in result

    assert "analysis" in result

    assert "recommendations" in result



def test_intelligence_orchestrator_keeps_pipeline_separate():

    service = IntelligenceOrchestrator()


    context = {

        "milk_variance":
            -25

    }


    result = service.evaluate(
        context
    )


    assert isinstance(
        result["signals"],
        list,
    )

    assert result["recommendations"] is not None
