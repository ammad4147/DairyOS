from datetime import datetime


from dairyos.herd.health.services.health_signal_service import (
    HealthSignalService
)

from dairyos.herd.health.services.health_correlation_service import (
    HealthCorrelationService
)



def test_multiple_signals_create_risk():

    signal_service = HealthSignalService()


    signals = [

        signal_service.detect_milk_drop(

            "HF-11001",

            20,

            30

        ),

        signal_service.detect_feed_drop(

            "HF-11001",

            18,

            24

        )

    ]


    result = HealthCorrelationService().evaluate(

        "HF-11001",

        signals

    )


    assert result.risk_level == "MEDIUM"



def test_history_increases_attention():

    signal_service = HealthSignalService()


    signals = [

        signal_service.detect_milk_drop(

            "HF-11002",

            20,

            30

        )

    ]


    result = HealthCorrelationService().evaluate(

        "HF-11002",

        signals,

        ["previous mastitis"]

    )


    assert result.risk_level == "HIGH"



def test_recommended_checks_exist():

    result = HealthCorrelationService().evaluate(

        "HF-11003",

        []

    )


    assert isinstance(

        result.recommended_checks,

        list

    )
