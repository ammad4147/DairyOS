from dairyos.herd.dashboard.services.predictive_signal_service import PredictiveSignalService



def test_signal_creation():

    signal = PredictiveSignalService().generate(

        "PRODUCTION",

        [1,2,3]

    )

    assert signal.category == "PRODUCTION"



def test_high_risk_pattern():

    signal = PredictiveSignalService().generate(

        "PRODUCTION",

        [1,2,3]

    )

    assert signal.risk == "HIGH"



def test_normal_pattern():

    signal = PredictiveSignalService().generate(

        "PRODUCTION",

        [1]

    )

    assert signal.risk == "NORMAL"



def test_confidence_growth():

    signal = PredictiveSignalService().generate(

        "HEALTH",

        [1,2,3,4]

    )

    assert signal.confidence == 90



def test_confidence_limit():

    signal = PredictiveSignalService().generate(

        "HEALTH",

        [1,2,3,4,5,6]

    )

    assert signal.confidence == 95



def test_production_action():

    signal = PredictiveSignalService().generate(

        "PRODUCTION",

        [1,2,3]

    )

    assert signal.recommended_action == "Review production factors"



def test_health_action():

    signal = PredictiveSignalService().generate(

        "HEALTH",

        [1,2,3]

    )

    assert signal.recommended_action == "Review animal health indicators"



def test_reproduction_action():

    signal = PredictiveSignalService().generate(

        "REPRODUCTION",

        [1,2,3]

    )

    assert signal.recommended_action == "Review breeding indicators"



def test_prediction_required():

    service = PredictiveSignalService()

    signal = service.generate(

        "FINANCE",

        [1,2,3]

    )

    assert service.requires_prediction_action(signal)



def test_model():

    signal = PredictiveSignalService().generate(

        "FINANCE",

        [1]

    )

    assert signal.category == "FINANCE"
