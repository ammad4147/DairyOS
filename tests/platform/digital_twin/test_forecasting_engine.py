from dairyos.platform.digital_twin.forecasting.services.forecast_engine import (
    ForecastEngine,
)



def test_forecast_generation():


    engine = ForecastEngine()



    forecast = engine.forecast(

        metric="milk_production",

        current_value=625,

        growth_rate=0.05,

        horizon_days=30,

    )



    assert forecast.predicted_value == 656.25


    assert forecast.confidence == 0.8

