from dairyos.intelligence.services.intelligence_analysis_service import (
    IntelligenceAnalysisService,
)

from dairyos.intelligence.models.intelligence_signal import (
    IntelligenceSignal,
)



def test_analysis_of_warning_signal():

    service = IntelligenceAnalysisService()


    signal = IntelligenceSignal(

        signal_type="MILK_VARIANCE",

        severity="WARNING",

        source="milk",

    )


    result = service.analyze(
        [signal]
    )


    assert result["status"] == "ATTENTION"

    assert result["priority"] == "MEDIUM"

    assert result["signals_count"] == 1



def test_analysis_of_critical_signal():

    service = IntelligenceAnalysisService()


    signal = IntelligenceSignal(

        signal_type="ANIMAL_HEALTH",

        severity="CRITICAL",

        source="health",

    )


    result = service.analyze(
        [signal]
    )


    assert result["status"] == "CRITICAL"

    assert result["priority"] == "HIGH"



def test_empty_analysis():

    service = IntelligenceAnalysisService()


    result = service.analyze([])


    assert result["status"] == "NORMAL"

    assert result["signals_count"] == 0
