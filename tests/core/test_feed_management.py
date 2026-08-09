from dairyos.herd.feed.services.feed_management_service import FeedManagementService



def test_feed_group():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.animal_group == "Lactating Cows"



def test_animal_count():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.animal_count == 25



def test_daily_feed_calculation():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.daily_feed_kg == 875



def test_daily_cost_calculation():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.daily_feed_cost == 62500



def test_cost_per_animal():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.cost_per_animal == 2500



def test_normal_status():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.status == "NORMAL"



def test_monitor_status():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        3000

    )

    assert result.status == "MONITOR"



def test_small_group():

    result = FeedManagementService().evaluate(

        "Heifers",

        10,

        20,

        1500

    )

    assert result.daily_feed_kg == 200



def test_feed_model():

    result = FeedManagementService().evaluate(

        "Dry Cows",

        5,

        25,

        1800

    )

    assert result.animal_group == "Dry Cows"



def test_feed_management_flow():

    result = FeedManagementService().evaluate(

        "Lactating Cows",

        25,

        35,

        2500

    )

    assert result.daily_feed_cost == 62500
