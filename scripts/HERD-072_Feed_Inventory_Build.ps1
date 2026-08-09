$ErrorActionPreference = "Stop"

Write-Host "Starting HERD-072 Feed Inventory Build"


New-Item -ItemType Directory -Force -Path `
"dairyos\inventory\feed\models",
"dairyos\inventory\feed\services",
"tests\core",
"scripts" | Out-Null



@'
from dataclasses import dataclass



@dataclass
class FeedInventory:


    feed_item: str

    available_quantity: float

    daily_consumption: float

    coverage_days: float

    status: str

    action: str
'@ | Set-Content `
"dairyos\inventory\feed\models\feed_inventory.py"



@'
from ..models.feed_inventory import FeedInventory



class FeedInventoryService:



    def evaluate(

        self,

        feed_item,

        available_quantity,

        daily_consumption

    ):


        if daily_consumption > 0:

            coverage_days = (

                available_quantity /

                daily_consumption

            )

        else:

            coverage_days = 0



        if coverage_days >= 30:

            status = "SECURE"

            action = "Continue normal procurement"


        elif coverage_days >= 7:

            status = "MONITOR"

            action = "Review upcoming purchase"


        else:

            status = "CRITICAL"

            action = "Immediate feed procurement required"



        return FeedInventory(

            feed_item,

            available_quantity,

            daily_consumption,

            coverage_days,

            status,

            action

        )
'@ | Set-Content `
"dairyos\inventory\feed\services\feed_inventory_service.py"



@'
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
'@ | Set-Content `
"tests\core\test_feed_inventory.py"



Write-Host "HERD-072 Feed Inventory Build Complete"