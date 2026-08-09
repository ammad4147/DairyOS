from dairyos.feed.intelligence import FeedCostService


def test_feed_cost_metric():

    service = FeedCostService()


    result = service.calculate_cost_metric(
        animal_group="MILKING_COWS",
        feed_cost=100000,
        milk_revenue=250000,
    )


    assert result.feed_cost == 100000
    assert result.milk_revenue == 250000
    assert result.feed_cost_ratio == 0.4
