from dairyos.herd.dashboard.services.risk_forecast_service import RiskForecastService



def test_forecast_creation():

    forecast = RiskForecastService().generate(

        "PRODUCTION",

        80,

        0

    )

    assert forecast.category == "PRODUCTION"



def test_high_risk():

    forecast = RiskForecastService().generate(

        "PRODUCTION",

        80,

        0

    )

    assert forecast.risk_level == "HIGH"



def test_medium_risk():

    forecast = RiskForecastService().generate(

        "HEALTH",

        40,

        15

    )

    assert forecast.risk_level == "MEDIUM"



def test_low_risk():

    forecast = RiskForecastService().generate(

        "FINANCE",

        20,

        5

    )

    assert forecast.risk_level == "LOW"



def test_probability_limit():

    forecast = RiskForecastService().generate(

        "HEALTH",

        90,

        20

    )

    assert forecast.probability == 95



def test_production_action():

    forecast = RiskForecastService().generate(

        "PRODUCTION",

        80,

        0

    )

    assert forecast.recommended_action == "Review feed and production factors"



def test_health_action():

    forecast = RiskForecastService().generate(

        "HEALTH",

        80,

        0

    )

    assert forecast.recommended_action == "Review animal health prevention"



def test_reproduction_action():

    forecast = RiskForecastService().generate(

        "REPRODUCTION",

        80,

        0

    )

    assert forecast.recommended_action == "Review breeding strategy"



def test_requires_action():

    service = RiskForecastService()

    forecast = service.generate(

        "PRODUCTION",

        80,

        0

    )

    assert service.requires_action(forecast)



def test_model():

    forecast = RiskForecastService().generate(

        "FINANCE",

        20,

        5

    )

    assert forecast.forecast == "FINANCE future risk forecast"
