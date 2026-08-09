from dairyos.intelligence.health.services.health_prediction_service import HealthPredictionService



def test_animal_id():

    result = HealthPredictionService().evaluate(

        "HF001",

        True,

        True,

        False

    )

    assert result.animal_id == "HF001"



def test_high_risk_score():

    result = HealthPredictionService().evaluate(

        "HF001",

        True,

        True,

        False

    )

    assert result.risk_score == 75



def test_high_risk_level():

    result = HealthPredictionService().evaluate(

        "HF001",

        True,

        True,

        False

    )

    assert result.risk_level == "HIGH"



def test_high_recommendation():

    result = HealthPredictionService().evaluate(

        "HF001",

        True,

        True,

        False

    )

    assert result.recommendation == "Veterinary review required"



def test_medium_risk():

    result = HealthPredictionService().evaluate(

        "HF002",

        True,

        False,

        False

    )

    assert result.risk_level == "MEDIUM"



def test_medium_action():

    result = HealthPredictionService().evaluate(

        "HF002",

        True,

        False,

        False

    )

    assert result.recommendation == "Monitor animal closely"



def test_low_risk():

    result = HealthPredictionService().evaluate(

        "HF003",

        False,

        False,

        False

    )

    assert result.risk_level == "LOW"



def test_low_action():

    result = HealthPredictionService().evaluate(

        "HF003",

        False,

        False,

        False

    )

    assert result.recommendation == "Continue normal observation"



def test_activity_change():

    result = HealthPredictionService().evaluate(

        "HF004",

        False,

        False,

        True

    )

    assert result.risk_score == 25



def test_prediction_service():

    assert HealthPredictionService is not None
