from dairyos.herd.dashboard.services.recommendation_service import RecommendationService



def test_recommendation_creation():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert len(result) == 1



def test_replacement_recommendation():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert result[0].category == "HERD STRATEGY"



def test_replacement_priority():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert result[0].priority == "HIGH"



def test_health_recommendation():

    result = RecommendationService().generate(

        health_alerts=2

    )

    assert result[0].category == "ANIMAL HEALTH"



def test_reproduction_recommendation():

    result = RecommendationService().generate(

        open_cows=5

    )

    assert result[0].category == "REPRODUCTION"



def test_finance_recommendation():

    result = RecommendationService().generate(

        financial_status="WARNING"

    )

    assert result[0].category == "FINANCE"



def test_production_recommendation():

    result = RecommendationService().generate(

        production_status="LOW"

    )

    assert result[0].category == "PRODUCTION"



def test_multiple_recommendations():

    result = RecommendationService().generate(

        health_alerts=1,

        replacement_shortage=True

    )

    assert len(result) == 2



def test_timeframe_exists():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert len(result[0].timeframe) > 0



def test_recommendation_text():

    result = RecommendationService().generate(

        replacement_shortage=True

    )

    assert len(result[0].recommendation) > 0
