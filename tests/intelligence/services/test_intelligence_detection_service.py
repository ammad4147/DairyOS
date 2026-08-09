from dairyos.intelligence.services.intelligence_detection_service import (
    IntelligenceDetectionService,
)


def test_milk_variance_detection():

    service = IntelligenceDetectionService()


    signal = service.detect_milk_variance(

        actual_litres=500,

        expected_litres=650,

    )


    assert signal is not None

    assert signal.signal_type == (
        "MILK_PRODUCTION_VARIANCE"
    )

    assert signal.source == (
        "milk_production"
    )

    assert signal.evidence["variance"] == -150



def test_no_signal_when_production_is_good():

    service = IntelligenceDetectionService()


    signal = service.detect_milk_variance(

        actual_litres=700,

        expected_litres=650,

    )


    assert signal is None

