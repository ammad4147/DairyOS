from dairyos.herd.health.services.health_signal_service import (
    HealthSignalService
)



def test_milk_drop_detection():

    result = HealthSignalService().detect_milk_drop(

        "HF-6001",

        20,

        30

    )


    assert result.signal_type == "MILK_YIELD_DROP"



def test_high_milk_drop():

    result = HealthSignalService().detect_milk_drop(

        "HF-6001",

        20,

        30

    )


    assert result.severity == "HIGH"



def test_feed_drop_detection():

    result = HealthSignalService().detect_feed_drop(

        "HF-6002",

        18,

        24

    )


    assert result.signal_type == "FEED_INTAKE_DROP"



def test_feed_drop_percentage():

    result = HealthSignalService().detect_feed_drop(

        "HF-6002",

        18,

        24

    )


    assert "25" in result.deviation



def test_normal_condition():

    result = HealthSignalService().detect_milk_drop(

        "HF-6003",

        29,

        30

    )


    assert result.severity == "NORMAL"
