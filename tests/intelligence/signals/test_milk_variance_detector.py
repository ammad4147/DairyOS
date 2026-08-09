from dairyos.intelligence.signals.detectors.milk_variance_detector import (
    MilkVarianceDetector,
)



def test_milk_variance_detector_generates_signal():

    detector = MilkVarianceDetector()


    signal = detector.detect(

        {
            "actual_litres": 70,
            "expected_litres": 100,
        }

    )


    assert signal is not None

    assert (
        signal.signal_type
        ==
        "MILK_PRODUCTION_VARIANCE"
    )



def test_milk_variance_detector_ignores_positive_variance():

    detector = MilkVarianceDetector()


    signal = detector.detect(

        {
            "actual_litres": 120,
            "expected_litres": 100,
        }

    )


    assert signal is None
