from dairyos.intelligence.feed.services.feed_optimization_service import FeedOptimizationService



def test_group():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.group_id == "LACTATING"



def test_feed_quantity():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.feed_quantity == 500



def test_milk_output():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.milk_output == 625



def test_efficiency():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.efficiency == 1.25



def test_good_status():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.status == "GOOD"



def test_good_recommendation():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        625

    )

    assert result.recommendation == "Maintain current ration"



def test_attention_status():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        450

    )

    assert result.status == "ATTENTION"



def test_attention_recommendation():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        450

    )

    assert result.recommendation == "Review ration efficiency"



def test_poor_status():

    result = FeedOptimizationService().evaluate(

        "LACTATING",

        500,

        300

    )

    assert result.status == "POOR"



def test_service_exists():

    assert FeedOptimizationService is not None
