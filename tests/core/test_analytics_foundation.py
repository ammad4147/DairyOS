from dairyos.analytics.services.analytics_service import AnalyticsService



def test_metric_name():

    result = AnalyticsService().evaluate(

        "Milk Production",

        625,

        "Litres",

        600

    )

    assert result.metric_name == "Milk Production"



def test_value():

    result = AnalyticsService().evaluate(

        "Milk Production",

        625,

        "Litres",

        600

    )

    assert result.value == 625



def test_unit():

    result = AnalyticsService().evaluate(

        "Milk Production",

        625,

        "Litres",

        600

    )

    assert result.unit == "Litres"



def test_positive_trend():

    result = AnalyticsService().evaluate(

        "Milk Production",

        625,

        "Litres",

        600

    )

    assert result.trend == "POSITIVE"



def test_positive_performance():

    result = AnalyticsService().evaluate(

        "Milk Production",

        625,

        "Litres",

        600

    )

    assert result.performance == "GOOD"



def test_negative_trend():

    result = AnalyticsService().evaluate(

        "Milk Production",

        500,

        "Litres",

        600

    )

    assert result.trend == "NEGATIVE"



def test_negative_performance():

    result = AnalyticsService().evaluate(

        "Milk Production",

        500,

        "Litres",

        600

    )

    assert result.performance == "ATTENTION"



def test_stable_trend():

    result = AnalyticsService().evaluate(

        "Milk Production",

        600,

        "Litres",

        600

    )

    assert result.trend == "STABLE"



def test_stable_performance():

    result = AnalyticsService().evaluate(

        "Milk Production",

        600,

        "Litres",

        600

    )

    assert result.performance == "GOOD"



def test_analytics_service():

    assert AnalyticsService is not None
