from dairyos.inventory.feed.services.feed_inventory_service import FeedInventoryService



def test_feed_item():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        120,

        2

    )

    assert result.feed_item == "Corn Silage"



def test_quantity():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        120,

        2

    )

    assert result.available_quantity == 120



def test_daily_consumption():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        120,

        2

    )

    assert result.daily_consumption == 2



def test_coverage():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        120,

        2

    )

    assert result.coverage_days == 60



def test_secure_status():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        120,

        2

    )

    assert result.status == "SECURE"



def test_secure_action():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        120,

        2

    )

    assert result.action == "Continue normal procurement"



def test_monitor_status():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        20,

        2

    )

    assert result.status == "MONITOR"



def test_critical_status():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        5,

        2

    )

    assert result.status == "CRITICAL"



def test_low_stock_action():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        5,

        2

    )

    assert result.action == "Immediate feed procurement required"



def test_inventory_flow():

    result = FeedInventoryService().evaluate(

        "Corn Silage",

        120,

        2

    )

    assert result.coverage_days == 60
