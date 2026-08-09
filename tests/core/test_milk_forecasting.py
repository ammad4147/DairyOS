from dairyos.intelligence.production.services.milk_forecast_service import MilkForecastService



def test_group():

    result = MilkForecastService().forecast(

        "LACTATING",

        625,

        600

    )

    assert result.group_id == "LACTATING"



def test_current_output():

    result = MilkForecastService().forecast(

        "LACTATING",

        625,

        600

    )

    assert result.current_output == 625



def test_historical_average():

    result = MilkForecastService().forecast(

        "LACTATING",

        625,

        600

    )

    assert result.historical_average == 600



def test_forecast_output():

    result = MilkForecastService().forecast(

        "LACTATING",

        625,

        600

    )

    assert result.forecast_output == 612.5



def test_increasing_trend():

    result = MilkForecastService().forecast(

        "LACTATING",

        625,

        600

    )

    assert result.trend == "INCREASING"



def test_positive_status():

    result = MilkForecastService().forecast(

        "LACTATING",

        625,

        600

    )

    assert result.status == "POSITIVE"



def test_decreasing_trend():

    result = MilkForecastService().forecast(

        "LACTATING",

        550,

        600

    )

    assert result.trend == "DECREASING"



def test_attention_status():

    result = MilkForecastService().forecast(

        "LACTATING",

        550,

        600

    )

    assert result.status == "ATTENTION"



def test_stable_status():

    result = MilkForecastService().forecast(

        "LACTATING",

        600,

        600

    )

    assert result.status == "NORMAL"



def test_service_exists():

    assert MilkForecastService is not None
