from dairyos.intelligence.feed.services.feed_optimization_service import FeedOptimizationService


def test_group():
    result = FeedOptimizationService().evaluate("LACTATING", 500, 625)
    assert result.group_id == "LACTATING"


def test_feed_quantity():
    result = FeedOptimizationService().evaluate("LACTATING", 500, 625)
    assert result.feed_quantity == 500


def test_milk_output():
    result = FeedOptimizationService().evaluate("LACTATING", 500, 625)
    assert result.milk_output == 625


def test_efficiency():
    result = FeedOptimizationService().evaluate("LACTATING", 500, 625)
    assert result.efficiency == 1.25


def test_attention_status_for_below_stage_appropriate_good_threshold():
    result = FeedOptimizationService().evaluate("LACTATING", 500, 625)
    assert result.status == "ATTENTION"


def test_attention_recommendation():
    result = FeedOptimizationService().evaluate("LACTATING", 500, 625)
    assert result.recommendation == "Review DMI, ration sorting, feed losses, health and lactation stage"


def test_poor_status():
    result = FeedOptimizationService().evaluate("LACTATING", 500, 300)
    assert result.status == "POOR"


def test_poor_recommendation():
    result = FeedOptimizationService().evaluate("LACTATING", 500, 300)
    assert result.recommendation == "Assess ration formulation, DMI, feed losses, health and body-condition trend"


def test_service_exists():
    assert FeedOptimizationService is not None
